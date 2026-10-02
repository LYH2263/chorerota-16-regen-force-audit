"""作废对调：重生成覆写格位时作废该周 pending 对调，详情指向履历编号。"""

VOIDED_STATUS = "voided"
ERR_SWAP_VOIDED = "swap_voided"


def void_pending(c, week_id: int, regen_id: int) -> int:
    """把该周所有 pending 对调置为 voided，并记录触发作废的履历编号。

    调用方负责 commit。返回作废条数。
    """
    cur = c.execute(
        "UPDATE swap_requests SET status=?, voided_by_regen_id=? "
        "WHERE week_id=? AND status='pending'",
        (VOIDED_STATUS, regen_id, week_id),
    )
    return cur.rowcount


def confirm_error(status: str):
    """对调确认门禁：作废对调不可确认。返回错误码或 None。"""
    if status == VOIDED_STATUS:
        return ERR_SWAP_VOIDED
    if status != "pending":
        return "not_pending"
    return None
