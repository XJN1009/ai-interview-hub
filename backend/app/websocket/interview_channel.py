import asyncio
import logging
from fastapi import WebSocket, WebSocketDisconnect, HTTPException
from pydantic import ValidationError
from app.core.database import SessionLocal
from app.models.interview import Interview
from app.models.user import User
from app.api.v1.realtime import authenticate_websocket, websocket_session_active
from app.api.v1.interviews import build_question_payload
from app.schemas.interview import InterviewAnswerRequest
from app.services.interview_core import submit_answer_core, finalize_interview, transition_interview, get_remaining_seconds

logger = logging.getLogger("websocket")


async def handle_interview_websocket(websocket: WebSocket, interview_id: int):
    user_id = await authenticate_websocket(websocket, "interview", interview_id)
    if user_id is None:
        return
    await websocket.accept()
    try:
        with SessionLocal() as db:
            interview = db.get(Interview, interview_id)
            await websocket.send_json({"type": "connected", "interview_id": interview_id,
                "status": interview.status, "version": interview.version,
                "remaining_seconds": get_remaining_seconds(interview)})
            current = next((q for q in interview.questions if q.seq == interview.current_question_seq), None)
            if current:
                await websocket.send_json({"type": "question", **build_question_payload(current, interview.status == "COMPLETED")})
        while True:
            if not websocket_session_active(websocket):
                await websocket.close(1008)
                return
            try:
                data = await asyncio.wait_for(websocket.receive_json(), timeout=30)
            except asyncio.TimeoutError:
                continue
            except (ValueError, TypeError):
                await websocket.send_json({"type": "error", "message": "消息必须为 JSON 对象"})
                continue
            if not isinstance(data, dict):
                await websocket.send_json({"type": "error", "message": "消息格式不正确"})
                continue
            if not websocket_session_active(websocket):
                await websocket.close(1008)
                return
            with SessionLocal() as db:
                interview = db.query(Interview).filter_by(id=interview_id, user_id=user_id).first()
                user = db.get(User, user_id)
                if not interview:
                    await websocket.close(1008)
                    return
                try:
                    event = data.get("type")
                    if event == "transcript_final":
                        req = InterviewAnswerRequest.model_validate(data)
                        result = await submit_answer_core(db, interview, user, req.text, req.duration_sec, req.skipped,
                                                         req.question_id, req.request_id, req.expected_version)
                        await websocket.send_json({"type": "evaluation", "answer_id": result["answer"].id,
                            "total_score": result["eval_res"]["score"], **result["eval_res"],
                            "version": result["version"], "is_finished": result["finished"],
                            "phase": result.get("phase"), "finished_qa": result.get("finished_qa")})
                        if result["next_question"]:
                            await websocket.send_json({"type": "next_question", **build_question_payload(result["next_question"])})
                        if result["finished"]:
                            # 逐题作答结束 → 进入反问环节（反问问答走 REST 端点），此处不再直接结算
                            await websocket.send_json({"type": "qa_finished", "phase": result.get("phase"),
                                                       "report_id": result["report_id"],
                                                       "report_state": result["report_state"]})
                    elif event in ("start", "pause", "resume", "abort"):
                        transition_interview(db, interview, event)
                        await websocket.send_json({"type": "state", "status": interview.status,
                            "version": interview.version, "remaining_seconds": get_remaining_seconds(interview)})
                    elif event == "finish":
                        rep = await finalize_interview(db, interview, user, force=True)
                        await websocket.send_json({"type": "finished", "report_id": rep.id})
                    elif event == "transcript_partial":
                        await websocket.send_json({"type": "transcript_partial", "text": str(data.get("text", ""))[:20000]})
                except (HTTPException, ValidationError) as exc:
                    db.rollback()
                    await websocket.send_json({"type": "error", "code": getattr(exc, "status_code", 422),
                        "message": exc.detail if isinstance(exc, HTTPException) else "消息缺少有效题目 ID 或请求 ID"})
                except Exception:
                    db.rollback()
                    logger.exception("实时面试处理失败")
                    await websocket.send_json({"type": "error", "message": "处理失败，已保存的答案可使用原请求重试"})
    except WebSocketDisconnect:
        pass
