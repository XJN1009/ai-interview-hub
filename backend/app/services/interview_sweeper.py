"""僵尸会话清扫（D6）：模拟面试不再限制提交时间，关页面/断网遗留的进行中面试需要兜底收尾。

判定口径用「最后一次活动」而不是 started_at：不限制提交时间后，一场面试合法地跑很久，
只有连续静默超过阈值才算僵尸。收尾分两档——
- 已有作答：强制结算出报告，不让已写的回答白答；
- 一题未答：置 CANCELLED（此时结算必然 409，空报告也没有意义）。
"""

import logging
import os
from datetime import datetime, timedelta
from typing import Dict, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.interview import Interview, InterviewAnswer, InterviewReverseQuestion
from app.models.user import User
from app.services.interview_core import finalize_interview, transition_interview

logger = logging.getLogger("interview_sweeper")

# 连续无活动多久判定为僵尸（小时）/ 清扫轮询间隔（秒）
ZOMBIE_IDLE_HOURS = float(os.getenv("INTERVIEW_ZOMBIE_IDLE_HOURS", "24"))
SWEEP_INTERVAL_SECONDS = int(os.getenv("INTERVIEW_SWEEP_INTERVAL_SECONDS", "600"))
# 单轮最多处理多少场，避免清扫本身拖垮请求处理
SWEEP_BATCH_LIMIT = 50
STALE_STATUSES = ("IN_PROGRESS", "PAUSED")


def _last_activity_at(db: Session, interview: Interview) -> datetime:
    """面试侧最近活动时间：作答与反问都算「人还在」。"""
    markers = [interview.created_at, interview.started_at, interview.paused_at]
    last_answer = (db.query(func.max(InterviewAnswer.created_at))
                   .filter(InterviewAnswer.interview_id == interview.id).scalar())
    last_reverse = (db.query(func.max(InterviewReverseQuestion.created_at))
                    .filter(InterviewReverseQuestion.interview_id == interview.id).scalar())
    markers += [last_answer, last_reverse]
    return max(m for m in markers if m is not None)


async def sweep_zombie_interviews(db: Session, idle_hours: float = ZOMBIE_IDLE_HOURS,
                                  now: Optional[datetime] = None) -> Dict[str, int]:
    """清扫僵尸会话，返回 {settled, cancelled, skipped}。skipped 含失败与仍在活动的场次。"""
    now = now or datetime.utcnow()
    cutoff = now - timedelta(hours=idle_hours)
    stat = {"settled": 0, "cancelled": 0, "skipped": 0}
    candidates = (db.query(Interview)
                  .filter(Interview.status.in_(STALE_STATUSES), Interview.created_at <= cutoff)
                  .order_by(Interview.created_at).limit(SWEEP_BATCH_LIMIT).all())
    for interview in candidates:
        if _last_activity_at(db, interview) > cutoff:
            stat["skipped"] += 1
            continue
        user = db.get(User, interview.user_id)
        if user is None:
            stat["skipped"] += 1
            continue
        has_answer = db.query(InterviewAnswer.id).filter(InterviewAnswer.interview_id == interview.id).first()
        try:
            if has_answer:
                await finalize_interview(db, interview, user, force=True)
                stat["settled"] += 1
                logger.info("僵尸面试 %s 已强制结算（静默超过 %s 小时）", interview.id, idle_hours)
            else:
                transition_interview(db, interview, "abort")
                stat["cancelled"] += 1
                logger.info("僵尸面试 %s 无任何作答，已置为 CANCELLED", interview.id)
        except Exception as exc:
            db.rollback()
            stat["skipped"] += 1
            logger.warning("僵尸面试 %s 收尾失败，下一轮重试：%s", interview.id, str(exc)[:200])
    return stat


async def run_zombie_sweeper_loop() -> None:
    """后台轮询任务：由 main.py 的 lifespan 启动，进程退出时取消。"""
    import asyncio

    from app.core.database import SessionLocal
    while True:
        await asyncio.sleep(SWEEP_INTERVAL_SECONDS)
        try:
            with SessionLocal() as db:
                stat = await sweep_zombie_interviews(db)
            if any(stat.values()):
                logger.info("僵尸会话清扫：结算 %s、中止 %s、跳过 %s",
                            stat["settled"], stat["cancelled"], stat["skipped"])
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("僵尸会话清扫轮次失败")
