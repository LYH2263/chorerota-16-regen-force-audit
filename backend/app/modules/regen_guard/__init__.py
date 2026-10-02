"""重生成门禁：决定本次生成请求是否放行。

- draft（或格表为空）：直接生成，无需履历。
- status=ready 且已有格：
  * 普通再生成（force 非真）→ 拒绝，格表内容保持不变；
  * force 但原因为空 → 拒绝（regen_reason_required）；
  * force 且原因非空 → 放行，由调用方写入重生成履历并覆写格位。
"""

# 普通再生成撞上已落位的 ready 周表
ERR_REQUIRES_FORCE = "regen_requires_force"
# force 重生成未提交非空原因
ERR_REASON_REQUIRED = "regen_reason_required"


def has_text(reason) -> bool:
    return bool(reason and str(reason).strip())


def evaluate(week_status: str, grid_count: int, force: bool, reason) -> dict:
    """纯函数门禁，返回 {ok, error}；放行时回传规范化后的 reason。"""
    locked = week_status == "ready" and grid_count > 0
    if not locked:
        return {"ok": True, "error": "", "reason": str(reason).strip() if has_text(reason) else ""}
    if not force:
        return {"ok": False, "error": ERR_REQUIRES_FORCE, "reason": ""}
    if not has_text(reason):
        return {"ok": False, "error": ERR_REASON_REQUIRED, "reason": ""}
    return {"ok": True, "error": "", "reason": str(reason).strip()}
