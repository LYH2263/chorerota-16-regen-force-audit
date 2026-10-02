import pytest
from fastapi.testclient import TestClient

from app.db import connect


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    from app.main import app
    with TestClient(app) as c:
        yield c


def grid_rows():
    c = connect()
    rows = [dict(r) for r in c.execute(
        "SELECT day,task_id,member_id FROM assignments WHERE week_id=1 ORDER BY id")]
    c.close()
    return rows


def regen_rows():
    c = connect()
    rows = [dict(r) for r in c.execute("SELECT * FROM regenerations ORDER BY id")]
    c.close()
    return rows


def test_draft_generates_without_history(client):
    r = client.post("/api/weeks/1/generate", json={})
    assert r.status_code == 200
    assert r.json()["regen_id"] is None
    assert r.json()["voided_swaps"] == 0
    assert regen_rows() == []  # draft 直接生成，无需履历


def test_plain_regenerate_fails_and_grid_unchanged(client):
    client.post("/api/weeks/1/generate", json={"days": 7})
    before = grid_rows()

    r = client.post("/api/weeks/1/generate", json={"days": 5})

    assert r.status_code == 409
    assert r.json()["detail"] == "regen_requires_force"
    assert grid_rows() == before  # 格表内容不变
    assert regen_rows() == []


def test_force_without_reason_rejected_and_grid_unchanged(client):
    client.post("/api/weeks/1/generate", json={"days": 7})
    before = grid_rows()

    for payload in ({"force": True}, {"force": True, "reason": ""}, {"force": True, "reason": "   "}):
        r = client.post("/api/weeks/1/generate", json=payload)
        assert r.status_code == 409
        assert r.json()["detail"] == "regen_reason_required"

    assert grid_rows() == before  # 格表内容不变
    assert regen_rows() == []


def _new_pending_swap(client, a_day, b_day):
    r = client.post("/api/weeks/1/swaps", json={
        "a_day": a_day, "a_task": 1, "b_day": b_day, "b_task": 2})
    assert r.status_code == 200, r.text
    return r.json()["id"]


def test_force_with_reason_writes_history_overwrites_and_voids_swaps(client):
    client.post("/api/weeks/1/generate", json={"days": 7})
    sid1 = _new_pending_swap(client, 0, 1)
    sid2 = _new_pending_swap(client, 2, 3)
    before = grid_rows()

    r = client.post("/api/weeks/1/generate",
                    json={"force": True, "reason": "  排班冲突需重排 ", "days": 5})

    assert r.status_code == 200, r.text
    body = r.json()
    assert body["voided_swaps"] == 2
    regen_id = body["regen_id"]
    assert regen_id is not None

    # 履历写入独立表，原因非空
    hist = regen_rows()
    assert len(hist) == 1
    assert hist[0]["id"] == regen_id and hist[0]["week_id"] == 1
    assert hist[0]["reason"] == "排班冲突需重排"

    # 格位被覆写（7 天 → 5 天），且内容确实变化
    after = grid_rows()
    assert after != before
    assert len(after) == body["count"]
    assert max(a["day"] for a in after) == 4

    # pending 对调全部作废，详情指向该履历编号
    c = connect()
    swaps = [dict(r) for r in c.execute(
        "SELECT id,status,voided_by_regen_id FROM swap_requests ORDER BY id")]
    c.close()
    assert {s["id"]: s["status"] for s in swaps} == {sid1: "voided", sid2: "voided"}
    assert all(s["voided_by_regen_id"] == regen_id for s in swaps)

    # 作废对调不可确认
    cr = client.post(f"/api/swaps/{sid1}/confirm", json={})
    assert cr.status_code == 400
    assert cr.json()["detail"] == "swap_voided"

    # 看板顶栏与履历列表同钉最近一次原因
    board = client.get("/api/weeks/1/board").json()
    assert board["latest_regen"]["id"] == regen_id
    assert board["latest_regen"]["reason"] == "排班冲突需重排"
    listed = client.get("/api/weeks/1/regenerations").json()
    assert listed[0] == board["latest_regen"]
