"""重生成履历仓储：regenerations 独立表的读写。"""
from datetime import datetime


def add(c, week_id: int, reason: str) -> int:
    """写入一条重生成履历，返回履历编号。调用方负责 commit。"""
    cur = c.execute(
        "INSERT INTO regenerations(week_id, reason, created_at) VALUES (?,?,?)",
        (week_id, reason.strip(), datetime.now().isoformat(timespec="seconds")),
    )
    return cur.lastrowid


def latest_for_week(c, week_id: int):
    """该周最近一次重生成履历（顶栏与履历列表同钉最近一次原因）。"""
    r = c.execute(
        "SELECT * FROM regenerations WHERE week_id=? ORDER BY id DESC LIMIT 1",
        (week_id,),
    ).fetchone()
    return dict(r) if r else None


def list_recent(c, week_id=None, limit=20):
    """履历列表，最近在前；可按周过滤。"""
    if week_id is None:
        rows = c.execute(
            "SELECT * FROM regenerations ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    else:
        rows = c.execute(
            "SELECT * FROM regenerations WHERE week_id=? ORDER BY id DESC LIMIT ?",
            (week_id, limit),
        ).fetchall()
    return [dict(r) for r in rows]
