import json
import logging
from datetime import datetime
from typing import Dict, Any
from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.core import state_machine
from app.models.interview import Interview, InterviewQuestion
from app.models.user import User
from app.api.v1.interviews import build_question_payload
from app.services.interview_core import (
    load_interview_context, get_remaining_seconds,
    submit_answer_core, finalize_interview
)

logger = logging.getLogger("websocket")

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, WebSocket] = {}

    async def connect(self, interview_id: int, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[interview_id] = websocket

    def disconnect(self, interview_id: int):
        if interview_id in self.active_connections:
            del self.active_connections[interview_id]

    async def send_json(self, interview_id: int, message: Dict[str, Any]):
        ws = self.active_connections.get(interview_id)
        if ws:
            await ws.send_text(json.dumps(message, ensure_ascii=False))

manager = ConnectionManager()


async def handle_interview_websocket(websocket: WebSocket, interview_id: int):
    """实时面试通道：答题/评分/追问/结算全部复用 interview_core 核心服务，
    与 REST 通道保持同一套状态机与业务逻辑。"""
    await manager.connect(interview_id, websocket)
    db: Session = SessionLocal()
    try:
        interview = db.query(Interview).filter(Interview.id == interview_id).first()
        if not interview:
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": "面试记录不存在"
            }))
            await websocket.close()
            return

        jd_text, resume_context = load_interview_context(interview, db)
        reveal = interview.status in ("COMPLETED", "CANCELLED", "EXPIRED")

        await manager.send_json(interview_id, {
            "type": "connected",
            "interview_id": interview_id,
            "status": interview.status,
            "current_seq": interview.current_question_seq,
            "total_questions": interview.total_questions,
            "remaining_seconds": get_remaining_seconds(interview)
        })

        current_q = db.query(InterviewQuestion).filter(
            InterviewQuestion.interview_id == interview_id,
            InterviewQuestion.seq == interview.current_question_seq
        ).first()

        if current_q:
            payload = build_question_payload(current_q, reveal_reference=reveal)
            payload["type"] = "question"
            await manager.send_json(interview_id, payload)

        while True:
            data_text = await websocket.receive_text()
            data = json.loads(data_text)
            event_type = data.get("type")

            if event_type == "transcript_partial":
                await manager.send_json(interview_id, {
                    "type": "transcript_partial",
                    "text": data.get("text", "")
                })

            elif event_type == "transcript_final":
                answer_text = (data.get("text") or "").strip()
                if not answer_text:
                    continue

                user = db.query(User).filter(User.id == interview.user_id).first()
                try:
                    result = await submit_answer_core(
                        db, interview, user,
                        text=answer_text,
                        duration_sec=data.get("duration_sec"),
                        speaking_rate=data.get("speaking_rate"),
                        filler_count=data.get("filler_count")
                    )
                except Exception as e:
                    # HTTPException 或其他错误统一以事件下发，不断开连接
                    detail = getattr(e, "detail", str(e))
                    await manager.send_json(interview_id, {
                        "type": "error",
                        "message": f"作答处理失败：{detail}"
                    })
                    continue

                eval_res = result["eval_res"]
                await manager.send_json(interview_id, {
                    "type": "evaluation",
                    "answer_id": result["answer"].id,
                    "total_score": eval_res["score"],
                    "dimensions": eval_res["dimensions"],
                    "evidence": eval_res["evidence"],
                    "weaknesses": eval_res["weaknesses"],
                    "missing_knowledge": eval_res["missing_knowledge"],
                    "suggestions": eval_res["suggestions"],
                    "next_action": eval_res.get("next_action"),
                    "is_followup": result["is_followup"]
                })

                next_q = result["next_question"]
                if next_q is not None:
                    payload = build_question_payload(next_q, reveal_reference=False)
                    payload["type"] = "next_question"
                    if result["is_followup"]:
                        payload["followup_notice"] = "AI 面试官根据你的回答追加了一道针对性问题"
                    await manager.send_json(interview_id, payload)

                if result["finished"]:
                    await manager.send_json(interview_id, {
                        "type": "finished",
                        "interview_id": interview_id,
                        "report_status": "COMPLETED",
                        "report_id": result.get("report_id"),
                        "report_url": f"/personal/interviews/{interview_id}/report"
                    })

            elif event_type == "pause":
                try:
                    state_machine.ensure(interview.status, state_machine.CAN_PAUSE, "暂停面试")
                    interview.status = "PAUSED"
                    db.commit()
                    await manager.send_json(interview_id, {"type": "paused"})
                except Exception as e:
                    await manager.send_json(interview_id, {
                        "type": "error", "message": getattr(e, "detail", str(e))
                    })

            elif event_type == "resume":
                try:
                    state_machine.ensure(interview.status, state_machine.CAN_RESUME, "继续面试")
                    interview.status = "IN_PROGRESS"
                    db.commit()
                    await manager.send_json(interview_id, {
                        "type": "resumed",
                        "remaining_seconds": get_remaining_seconds(interview)
                    })
                except Exception as e:
                    await manager.send_json(interview_id, {
                        "type": "error", "message": getattr(e, "detail", str(e))
                    })

            elif event_type == "finish":
                user = db.query(User).filter(User.id == interview.user_id).first()
                try:
                    rep = await finalize_interview(db, interview, user, force=True)
                    await manager.send_json(interview_id, {
                        "type": "finished",
                        "interview_id": interview_id,
                        "report_id": rep.id,
                        "total_score": rep.total_score,
                        "report_url": f"/personal/interviews/{interview_id}/report"
                    })
                except Exception as e:
                    await manager.send_json(interview_id, {
                        "type": "error", "message": getattr(e, "detail", str(e))
                    })

            elif event_type == "abort":
                try:
                    state_machine.ensure(interview.status, state_machine.CAN_ABORT, "中止面试")
                    interview.status = "CANCELLED"
                    interview.ended_at = datetime.utcnow()
                    db.commit()
                    await manager.send_json(interview_id, {"type": "aborted"})
                except Exception as e:
                    await manager.send_json(interview_id, {
                        "type": "error", "message": getattr(e, "detail", str(e))
                    })

    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        manager.disconnect(interview_id)
        db.close()
