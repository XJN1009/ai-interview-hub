"""面试会话状态机：集中声明合法迁移，非法迁移在入口拦截（HTTP 409）。

状态：CREATED → READY → IN_PROGRESS ⇄ PAUSED → COMPLETED / CANCELLED / EXPIRED
- READY→IN_PROGRESS：开始面试
- IN_PROGRESS→PAUSED/IN_PROGRESS：暂停/继续
- READY/IN_PROGRESS/PAUSED→COMPLETED：交卷结算（含提前交卷）
- READY/IN_PROGRESS/PAUSED→CANCELLED：中止（不生成报告）
- COMPLETED/CANCELLED/EXPIRED 为终态，任何操作拒绝。
"""

from fastapi import HTTPException

# 允许作答/推进的状态
ANSWERABLE = {"READY", "IN_PROGRESS", "PAUSED"}
# 可以流转到 IN_PROGRESS 的来源状态
CAN_START = {"CREATED", "READY", "PAUSED"}
CAN_PAUSE = {"IN_PROGRESS"}
CAN_RESUME = {"PAUSED"}
# 可以结算（finish）的来源状态
CAN_FINISH = {"READY", "IN_PROGRESS", "PAUSED"}
# 可以中止（abort）的来源状态
CAN_ABORT = {"CREATED", "READY", "IN_PROGRESS", "PAUSED"}
# 终态
TERMINAL = {"COMPLETED", "CANCELLED", "EXPIRED"}


def ensure(current: str, allowed: set, action: str) -> None:
    """当前状态不在 allowed 内时抛 409。"""
    if current not in allowed:
        raise HTTPException(
            status_code=409,
            detail=f"当前面试状态为【{current}】，不允许执行【{action}】"
        )


def ensure_not_terminal(current: str, action: str) -> None:
    if current in TERMINAL:
        raise HTTPException(
            status_code=409,
            detail=f"面试已处于终态【{current}】，不允许再【{action}】"
        )
