"""面试核心业务服务：REST 与 WebSocket 两条通道共用的答题、推进、结算逻辑。

抽取动机（修复 A 类问题）：
- 两通道此前各写一份答题/结算逻辑，出现 WS 重复创建 AnswerEvaluation、
  finish 通道 competency_name 写死 "Redis" 等分叉；
- next_action 自适应追问在整卷预生成后失效：现按评分建议从题库换/插追问题并后移卷面；
- 整场时长以服务端 started_at 正计时（不限制提交时间），前端刷新不再重置。
"""

import json
import logging
from datetime import datetime, timedelta
import hashlib
import uuid
from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_, update, func
from sqlalchemy.exc import IntegrityError
from app.ai.schemas import AnswerEvalSchema
from app.services.ai_provenance import ai_context, RUBRIC_VERSION
from app.services.learning import generate_and_store_learning_plan, resolve_target_job

from app.ai.provider import ai_provider
from app.core import state_machine
from app.models.interview import (
    Interview, InterviewAnswer, InterviewQuestion, AnswerEvaluation, InterviewReport,
    InterviewReverseQuestion
)
from app.models.job import Job
from app.models.profile import CompetencyHistory, UserCompetency
from app.models.question import QuestionBank
from app.models.resume import Resume
from app.models.user import User

logger = logging.getLogger("interview_service")

# 允许追问插入的次数上限（每场面试）
MAX_FOLLOWUP_INSERTS = 2

# 反问环节：候选人最多可提的反问条数
MAX_REVERSE_QUESTIONS = 3

DIFF_ORDER = ["EASY", "MEDIUM", "HARD"]


def build_jd_text(job: Optional[Job] = None, override: str = None) -> str:
    """优先使用用户输入/自动带出的 JD 文本，否则回退到岗位自身的 JD 字段。"""
    if override and override.strip():
        return override.strip()
    if not job:
        return ""
    parts = [
        f"岗位名称：{job.title}",
        f"学历要求：{job.education}｜经验要求：{job.experience}｜工作城市：{job.city}",
    ]
    if job.skills:
        parts.append("技能要求：" + "、".join(s.skill_name for s in job.skills))
    if job.description:
        parts.append(f"岗位描述：{job.description}")
    if job.duties:
        parts.append(f"岗位职责：{job.duties}")
    if job.requirements:
        parts.append(f"任职要求：{job.requirements}")
    if job.bonus:
        parts.append(f"加分项：{job.bonus}")
    return "\n".join(parts)


def build_resume_context(resume: Optional[Resume] = None) -> str:
    """将结构化简历序列化为供 AI 使用的文本上下文。"""
    if not resume:
        return ""
    lines = [f"姓名：{resume.name}｜目标岗位：{resume.target_job_title}"]
    for e in resume.educations:
        lines.append(f"教育：{e.school} {e.major} {e.degree}（{e.start_date}~{e.end_date}）")
    for w in resume.work_experiences:
        lines.append(f"工作：{w.company} - {w.title}（{w.start_date}~{w.end_date}）：{w.description}")
    for p in resume.projects:
        lines.append(f"项目：{p.name}（{p.role}，{p.technologies}）：{p.description}")
    if resume.skills:
        lines.append("技能：" + "、".join(f"{s.skill_name}({s.level})" for s in resume.skills))
    return "\n".join(lines)


def load_interview_context(interview: Interview, db: Session) -> Tuple[str, str]:
    """加载一次面试的 JD 与简历上下文（用于出题与评分）。"""
    job = db.query(Job).filter(Job.id == interview.job_id).first() if interview.job_id else None
    resume = db.query(Resume).filter(Resume.id == interview.resume_id).first() if interview.resume_id else None
    return build_jd_text(job, interview.jd_text), build_resume_context(resume)


def get_elapsed_seconds(interview: Interview) -> Optional[int]:
    """以服务端 started_at 为准的整场已用秒数；未开始返回 None。

    模拟面试不限制提交时间（D6），因此这里只做如实计时：暂停期间冻结在 paused_at，
    duration_minutes 退化为「预计时长」，仅用于开场文案与配比参考，不参与任何截止判定。
    """
    if not interview.started_at:
        return None
    now = interview.paused_at if interview.status == "PAUSED" and interview.paused_at else datetime.utcnow()
    return max(0, int((now - interview.started_at).total_seconds()))


# 超时轻扣分：每超时 30 秒扣 3 分，最多扣 15 分（惩罚紧张学生但不归零）
OVERTIME_PENALTY_PER_30S = 3.0
OVERTIME_PENALTY_MAX = 15.0


def mark_question_shown(interview: Interview) -> None:
    """记录当前题呈现时间（服务端单题计时锚点）。"""
    interview.current_question_shown_at = datetime.utcnow()


def measure_question_usage(interview: Interview, question: InterviewQuestion,
                           client_duration: Optional[int]) -> Tuple[int, int, bool]:
    """服务端口径计算本题真实用时。

    返回 (真实用时秒, 超时秒, 是否超时)。
    - 有呈现时间：以 utcnow - shown_at 为准（不信任客户端上报）；
    - 无呈现时间（历史数据/旧会话）：退回客户端上报值。
    """
    limit = question.time_limit_sec or 180
    if interview.current_question_shown_at:
        elapsed = int((datetime.utcnow() - interview.current_question_shown_at).total_seconds())
        elapsed = max(0, min(elapsed, 3600))
    else:
        elapsed = max(0, min(int(client_duration or 0), 3600))
    overtime_sec = max(0, elapsed - limit)
    return elapsed, overtime_sec, overtime_sec > 0


def apply_overtime_penalty(score: float, overtime_sec: int) -> float:
    """超时轻扣分：按比例扣分并设下限，保证不因超时直接归零。"""
    if overtime_sec <= 0:
        return score
    penalty = min(OVERTIME_PENALTY_MAX,
                  (overtime_sec // 30 + (1 if overtime_sec % 30 else 0)) * OVERTIME_PENALTY_PER_30S)
    return round(max(0.0, score - penalty), 1)


def empty_answer_evaluation(question_text: str) -> Dict[str, Any]:
    """空作答：直接 0 分并给出明确提示，不消耗一次 LLM 调用。"""
    return {
        "score": 0.0,
        "dimensions": {
            "professional": 0.0, "relevance": 0.0, "completeness": 0.0,
            "logic": 0.0, "depth": 0.0, "communication": 0.0,
        },
        "evidence": ["本次未提交任何有效作答内容，无法进行能力评估"],
        "weaknesses": ["空作答：可能是主动放弃、时间不足或对题目完全陌生"],
        "missing_knowledge": ["需先厘清题目考察的核心概念，再组织至少 3 句的结构化回答"],
        "suggestions": [
            "面试中即使不确定，也应先复述问题要点、再给出思路框架与已知相关信息，避免留白",
            f"回顾题目：{question_text[:60]}{'…' if len(question_text) > 60 else ''}"
        ],
        "next_action": "BASIC",
    }


def skip_answer_evaluation(question_text: str) -> Dict[str, Any]:
    """主动跳过：0 分但评语温和，不产生严厉负面反馈（区别于空作答/超时）。"""
    return {
        "score": 0.0,
        "dimensions": {
            "professional": 0.0, "relevance": 0.0, "completeness": 0.0,
            "logic": 0.0, "depth": 0.0, "communication": 0.0,
        },
        "evidence": ["候选人主动标记跳过本题，未提交作答"],
        "weaknesses": ["本题被主动跳过：可能是超出当前知识范围，或希望将时间留给后续题目"],
        "missing_knowledge": [f"建议复盘时重点关注：{question_text[:60]}{'…' if len(question_text) > 60 else ''}"],
        "suggestions": [
            "主动跳过是一种合理的时间管理策略，面试结束后可针对此题定向补强",
            "建议将此题加入「错题本 / 重点复盘清单」，后续做专项训练"
        ],
        "next_action": "BASIC",
    }


def build_ai_reference_points(job_title: str, question_text: str) -> List[str]:
    """AI 动态生成题的参考答案要点兜底（无预置要点时给出通用复盘指引）。"""
    return [
        f"围绕【{job_title}】岗位的核心要求展开，明确回答的结论与适用前提",
        "给出原理/机制层面的解释，而不是只罗列使用方式或名词",
        "结合候选人自己项目中的真实场景与量化数据佐证",
        "主动说明方案的边界、代价与被放弃的备选方案及原因",
        f"题目回顾：{question_text[:60]}{'…' if len(question_text) > 60 else ''}"
    ]


def parse_ref_points(raw: Optional[str]) -> Optional[List[str]]:
    if not raw:
        return None
    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, list) else None
    except Exception:
        return None


def _paper_meta(interview: Interview, db: Session) -> Dict[str, Any]:
    plan = interview.plan
    meta: Dict[str, Any] = {}
    if plan and plan.paper_json:
        try:
            meta = json.loads(plan.paper_json) or {}
        except Exception:
            meta = {}
    return meta


async def _maybe_followup(
    db: Session, interview: Interview, curr_q: InterviewQuestion,
    eval_res: Dict[str, Any]
) -> Optional[InterviewQuestion]:
    """next_action 自适应追问：按评分建议从题库选同技能不同题干的题，插入当前题之后。

    - FOLLOW_UP/DEEP：答得好 → 同技能更高难度题；BASIC：答得差 → 同技能更低难度题。
    - 每场最多插入 MAX_FOLLOWUP_INSERTS 次；题库无合适题则放弃追问（不阻断流程）。
    - 插入方式：seq >= 当前题+1 的题目整体后移一位，追问题占下一槽位；总题数 +1。
    """
    action = (eval_res.get("next_action") or "").upper()
    if action not in ("FOLLOW_UP", "DEEP", "BASIC", "SIMPLIFY"):
        return None

    meta = _paper_meta(interview, db)
    if meta.get("followup_count", 0) >= MAX_FOLLOWUP_INSERTS:
        return None

    idx = DIFF_ORDER.index(curr_q.difficulty) if curr_q.difficulty in DIFF_ORDER else 1
    if action in ("BASIC", "SIMPLIFY"):
        target_diffs = DIFF_ORDER[:idx] or ["EASY"]
    else:
        target_diffs = DIFF_ORDER[idx + 1:] or ["HARD"]

    used_texts = {q.text for q in interview.questions}
    cand = db.query(QuestionBank).filter(
        QuestionBank.enabled == True,  # noqa: E712
        QuestionBank.skill_name == curr_q.skill_name,
        QuestionBank.difficulty.in_(target_diffs)
    ).all()
    cand = [c for c in cand if c.text not in used_texts]
    if not cand:
        # 同技能没有合适题就不追问，保持原卷面
        return None
    cand.sort(key=lambda c: (c.usage_count or 0, c.id))
    picked = cand[0]

    # 后移槽位：倒序更新避免中间态 seq 冲突
    following = (db.query(InterviewQuestion)
                 .filter(InterviewQuestion.interview_id == interview.id,
                         InterviewQuestion.seq > curr_q.seq)
                 .order_by(InterviewQuestion.seq.desc()).all())
    for q in following:
        q.seq = q.seq + 1

    ref_points = parse_ref_points(picked.reference_points_json) or []
    fu = InterviewQuestion(
        interview_id=interview.id,
        parent_question_id=curr_q.id,
        seq=curr_q.seq + 1,
        stage=picked.stage or curr_q.stage,
        question_type=picked.question_type,
        skill_name=picked.skill_name,
        text=picked.text,
        difficulty=picked.difficulty,
        bank_id=picked.id,
        reference_points_json=json.dumps(ref_points, ensure_ascii=False),
        hints=picked.hints,
        time_limit_sec=picked.time_limit_sec or 180,
        source="QUESTION_BANK"
    )
    db.add(fu)
    picked.usage_count = (picked.usage_count or 0) + 1
    interview.total_questions = (interview.total_questions or 0) + 1

    meta["followup_count"] = meta.get("followup_count", 0) + 1
    meta["total_after_followup"] = interview.total_questions
    if interview.plan:
        interview.plan.paper_json = json.dumps(meta, ensure_ascii=False)
        interview.plan.total_questions = interview.total_questions
    db.flush()
    logger.info(f"interview={interview.id} 插入追问（{action}）bank_id={picked.id} seq={fu.seq}")
    return fu


LEASE_SECONDS = 180


def _lease_available():
    return or_(Interview.processing_token.is_(None),
               Interview.processing_started_at < datetime.utcnow() - timedelta(seconds=LEASE_SECONDS))


def transition_interview(db, interview, action):
    """REST/WS 共用，处理评分或报告时不允许另一通道改变会话状态。"""
    db.refresh(interview)
    allowed = {"start": state_machine.CAN_START, "pause": state_machine.CAN_PAUSE,
               "resume": state_machine.CAN_RESUME, "abort": state_machine.CAN_ABORT}[action]
    state_machine.ensure(interview.status, allowed, action)
    now = datetime.utcnow()
    values = {"version": interview.version + 1}
    if action == "pause":
        values.update(status="PAUSED", paused_at=now)
    elif action == "abort":
        values.update(status="CANCELLED", ended_at=now)
    else:
        values.update(status="IN_PROGRESS")
        # 开场环节：用户点击「开始面试」后进入逐题作答，环节标记随之推进。
        # 只在仍处于 OPENING 时推进，避免从 PAUSED 恢复时把反问环节打回 QA。
        if (interview.phase or "QA") == "OPENING":
            values["phase"] = "QA"
        if interview.status == "PAUSED" and interview.paused_at:
            gap = now - interview.paused_at
            values.update(paused_at=None)
            if interview.started_at:
                values["started_at"] = interview.started_at + gap
            if interview.current_question_shown_at:
                values["current_question_shown_at"] = interview.current_question_shown_at + gap
        else:
            values["started_at"] = interview.started_at or now
            values["current_question_shown_at"] = interview.current_question_shown_at or now
    changed = db.query(Interview).filter(Interview.id == interview.id, Interview.version == interview.version,
                                        _lease_available()).update(values, synchronize_session=False)
    if not changed:
        db.rollback()
        raise HTTPException(409, "会话正在处理作答或报告，请稍后重试")
    db.commit()
    db.refresh(interview)


def _replay(db, answer):
    result = json.loads(answer.result_json)
    next_id = result.pop("next_question_id", None)
    result["answer"] = answer
    result["next_question"] = db.get(InterviewQuestion, next_id) if next_id else None
    if result.get("finished"):
        interview = db.get(Interview, answer.interview_id)
        if interview:
            result["report_state"] = interview.report_state
            result["report_id"] = interview.report.id if interview.report else None
    result["replayed"] = True
    return result


async def submit_answer_core(db: Session, interview: Interview, user: User, text: str,
                             duration_sec: Optional[int] = None, skipped: bool = False,
                             question_id: int = None, request_id: str = None,
                             expected_version: int = None) -> Dict[str, Any]:
    if interview.user_id != user.id:
        raise HTTPException(403, "无权作答此面试")
    if not question_id or not request_id:
        raise HTTPException(422, "提交作答必须携带 question_id 与 request_id")
    fingerprint = hashlib.sha256(json.dumps([text, skipped], ensure_ascii=False).encode()).hexdigest()
    curr_q = db.query(InterviewQuestion).filter_by(id=question_id, interview_id=interview.id).first()
    if not curr_q:
        raise HTTPException(409, "题目不属于本次面试")
    request_answer = db.query(InterviewAnswer).filter_by(interview_id=interview.id, request_id=request_id).first()
    if request_answer and (request_answer.question_id != question_id or request_answer.payload_hash != fingerprint):
        raise HTTPException(409, "同一请求 ID 不能用于不同题目或不同答案")
    existing = db.query(InterviewAnswer).filter_by(question_id=question_id).first()
    if existing and existing.result_json:
        if existing.request_id != request_id or existing.payload_hash != fingerprint:
            raise HTTPException(409, "此题已完成作答，请刷新会话获取下一题")
        return _replay(db, existing)
    if existing and existing.evaluation:
        raise HTTPException(409, "此题已有历史评分，不能重复评分")
    if existing and existing.payload_hash and existing.payload_hash != fingerprint:
        raise HTTPException(409, "已保存本题答案，请使用原答案和原请求重试")
    db.refresh(interview)
    state_machine.ensure(interview.status, state_machine.ANSWERABLE, "提交作答")
    if curr_q.seq != interview.current_question_seq:
        raise HTTPException(409, "当前题目已变化，请刷新会话")
    if expected_version is not None and expected_version != interview.version:
        raise HTTPException(409, "会话版本已变化，请刷新会话")
    lease = uuid.uuid4().hex
    claimed = db.query(Interview).filter(Interview.id == interview.id, Interview.version == interview.version,
                                         Interview.status == "IN_PROGRESS", _lease_available()).update(
        {"processing_token": lease, "processing_started_at": datetime.utcnow()}, synchronize_session=False)
    if not claimed:
        db.rollback()
        raise HTTPException(409, "本题正在评分，请使用同一请求 ID 稍后重试")
    db.commit()
    answer = existing
    try:
        db.refresh(interview)
        real_duration, overtime_sec, is_overtime = measure_question_usage(interview, curr_q, duration_sec)
        if not answer:
            answer = InterviewAnswer(question_id=curr_q.id, interview_id=interview.id, user_id=user.id,
                                     text=text, duration_sec=real_duration, overtime=is_overtime,
                                     overtime_sec=overtime_sec, speaking_rate=0, filler_count=0)
            db.add(answer)
        answer.request_id, answer.payload_hash = request_id, fingerprint
        answer.processing_state = "PROCESSING"
        db.commit()  # 答案先持久化，外部模型调用时不持有数据库写事务。
        jd_text, resume_context = load_interview_context(interview, db)
        is_empty = not (text or "").strip()
        if skipped or is_empty:
            eval_res = skip_answer_evaluation(curr_q.text) if skipped else empty_answer_evaluation(curr_q.text)
            provenance = {"source": "RULE", "model": "local-rule", "rubric_version": RUBRIC_VERSION}
        else:
            with ai_context(user.id, interview.id, request_id):
                eval_res = await ai_provider.evaluate_answer(curr_q.text, text, curr_q.seq,
                    jd_text=jd_text or None, resume_context=resume_context or None,
                    reference_points=parse_ref_points(curr_q.reference_points_json))
            provenance = eval_res.pop("_ai_meta", {"source": "UNKNOWN", "model": "unknown"})
            if interview.type == "ENTERPRISE_RECRUITMENT" and provenance.get("source") != "REAL":
                raise HTTPException(503, "企业正式面试的模型评分不可用，答案已保存，可稍后重试")
        eval_res = AnswerEvalSchema.model_validate(eval_res).model_dump()
        # Rubric 数值由服务端统一加权，模型不能另给一个互相矛盾的总分。
        weights = {"professional": .30, "relevance": .20, "completeness": .15,
                   "logic": .15, "depth": .15, "communication": .05}
        raw_score = round(sum(eval_res["dimensions"][k] * w for k, w in weights.items()), 1)
        eval_res["score"] = apply_overtime_penalty(raw_score, answer.overtime_sec)
        eval_res["provenance"] = provenance
        if answer.overtime:
            eval_res["evidence"].append(f"超出建议限时 {answer.overtime_sec} 秒，评分由 {raw_score} 调整为 {eval_res['score']}")
        # 缺题补题也在数据库写事务之前完成。
        missing_data = None
        if curr_q.seq < interview.total_questions and not db.query(InterviewQuestion).filter_by(
                interview_id=interview.id, seq=curr_q.seq + 1).first():
            with ai_context(user.id, interview.id, request_id):
                missing_data = await ai_provider.generate_question(job_title=interview.job.title if interview.job else "综合岗位",
                    seq=curr_q.seq + 1, difficulty=interview.difficulty, last_question=curr_q.text,
                    last_answer=text, last_score=eval_res["score"], jd_text=jd_text or None,
                    used_texts=[q.text for q in interview.questions])
        db.expire_all()
        db.refresh(interview)
        if interview.processing_token != lease or interview.status != "IN_PROGRESS":
            raise HTTPException(409, "处理租约已变化，请使用原请求重试")
        # CAS 获得写锁，阻止过期租约的其他工作线程并发落库。
        locked = db.query(Interview).filter_by(id=interview.id, processing_token=lease).update(
            {"processing_started_at": datetime.utcnow()}, synchronize_session=False)
        if not locked:
            raise HTTPException(409, "处理租约已变化")
        evaluation = AnswerEvaluation(answer_id=answer.id, interview_id=interview.id,
            total_score=eval_res["score"], dimensions_json=json.dumps(eval_res["dimensions"], ensure_ascii=False),
            evidence_json=json.dumps(eval_res["evidence"], ensure_ascii=False),
            weaknesses_json=json.dumps(eval_res["weaknesses"], ensure_ascii=False),
            missing_knowledge_json=json.dumps(eval_res["missing_knowledge"], ensure_ascii=False),
            suggestions_json=json.dumps(eval_res["suggestions"], ensure_ascii=False),
            next_action=eval_res["next_action"], provenance_json=json.dumps(provenance, ensure_ascii=False))
        db.add(evaluation)
        followup = await _maybe_followup(db, interview, curr_q, eval_res)
        next_q = followup or db.query(InterviewQuestion).filter_by(interview_id=interview.id, seq=curr_q.seq + 1).first()
        if next_q is None and curr_q.seq < interview.total_questions:
            if not missing_data or not missing_data.get("question"):
                raise HTTPException(503, "下一题生成失败，答案已保存，请重试")
            next_q = InterviewQuestion(interview_id=interview.id, seq=curr_q.seq + 1,
                text=missing_data["question"], skill_name=missing_data["skill_name"], stage=missing_data["stage"],
                difficulty=missing_data["difficulty"], question_type=missing_data.get("question_type") or "PROFESSIONAL",
                source="AI_GENERATED", time_limit_sec=missing_data.get("time_limit_sec") or 180)
            db.add(next_q)
        db.flush()
        finished = next_q is None
        if finished:
            # 逐题作答结束：不再直接结算，改为进入反问环节（真实面试标配），
            # 由用户「跳过反问」或「交卷」收尾；status 仍为 IN_PROGRESS，故状态机行为不变。
            interview.phase = "REVERSE"
            interview.current_question_shown_at = None
        else:
            interview.current_question_seq = next_q.seq
            mark_question_shown(interview)
        interview.version += 1
        interview.processing_token, interview.processing_started_at = None, None
        result = {"eval_res": eval_res, "next_question_id": next_q.id if next_q else None,
                  "is_followup": followup is not None, "finished": finished, "report_id": None,
                  "report_state": interview.report_state, "version": interview.version,
                  "total_questions": interview.total_questions, "raw_score": raw_score,
                  "overtime": answer.overtime, "overtime_sec": answer.overtime_sec,
                  "is_empty": is_empty, "is_skipped": skipped, "elapsed_seconds": get_elapsed_seconds(interview),
                  # 逐题作答结束即进入反问环节，前端据此切换到反问卡片
                  "phase": interview.phase, "finished_qa": finished}
        answer.processing_state = "COMPLETED"
        answer.result_json = json.dumps(result, ensure_ascii=False)
        db.commit()  # 评分、追问、推进和幂等响应一次提交。
    except Exception:
        db.rollback()
        released = db.query(Interview).filter_by(id=interview.id, processing_token=lease).update(
            {"processing_token": None, "processing_started_at": None}, synchronize_session=False)
        if released and answer is not None:
            db.query(InterviewAnswer).filter_by(id=answer.id, processing_state="PROCESSING").update({"processing_state": "FAILED"})
        db.commit()
        raise
    return _replay(db, answer)


def _reverse_state(interview: Interview, db: Session) -> Dict[str, Any]:
    """反问环节当前状态（供 GET 与提交后回显共用）：只有候选人自己的提问。"""
    rows = (db.query(InterviewReverseQuestion)
            .filter_by(interview_id=interview.id).order_by(InterviewReverseQuestion.seq).all())
    return {
        "phase": interview.phase or "QA",
        "max_count": MAX_REVERSE_QUESTIONS,
        "used_count": len(rows),
        "remaining": max(0, MAX_REVERSE_QUESTIONS - len(rows)),
        "questions": [{"seq": r.seq, "candidate_text": r.candidate_text} for r in rows],
    }


def get_reverse_state(db: Session, interview: Interview, user: User) -> Dict[str, Any]:
    if interview.user_id != user.id:
        raise HTTPException(403, "无权查看此面试的反问记录")
    return _reverse_state(interview, db)


def _next_reverse_seq(db: Session, interview_id: int) -> int:
    """按已有最大 seq 推导下一条编号；count() 在历史数据有缺口时会撞号。"""
    return (db.query(func.max(InterviewReverseQuestion.seq))
            .filter(InterviewReverseQuestion.interview_id == interview_id).scalar() or 0) + 1


def submit_reverse_question_core(db: Session, interview: Interview, user: User,
                                 text: str, request_id: str) -> Dict[str, Any]:
    """记录一条反问：只登记候选人的提问，AI 不作答、不点评、不计分。

    零成本落在三处：不发起 LLM 调用（无 token、无等待）、不进入任何计分路径、
    不占用单题限时。幂等口径与逐题作答一致：同一 (interview_id, request_id)
    只生效一次，超时重发或刷新后重提直接回读既有记录。
    """
    if interview.user_id != user.id:
        raise HTTPException(403, "无权在此面试中提问")
    db.refresh(interview)
    if (interview.phase or "QA") != "REVERSE":
        raise HTTPException(409, "当前不在反问环节，无法提交提问")
    content = (text or "").strip()
    if not content:
        raise HTTPException(422, "提问内容不能为空")
    replay = db.query(InterviewReverseQuestion).filter_by(
        interview_id=interview.id, request_id=request_id).first()
    if replay:
        # 与逐题作答同一口径：同一 request_id 换内容不属于重发，静默丢弃会误导用户
        if replay.candidate_text != content:
            raise HTTPException(409, "该请求已提交过其他提问内容，请重新输入后提交")
        return _reverse_state(interview, db)
    used = db.query(InterviewReverseQuestion).filter_by(interview_id=interview.id).count()
    if used >= MAX_REVERSE_QUESTIONS:
        raise HTTPException(422, f"反问最多 {MAX_REVERSE_QUESTIONS} 条，请直接交卷或跳过")

    seq = _next_reverse_seq(db, interview.id)
    row = InterviewReverseQuestion(
        interview_id=interview.id, seq=seq, request_id=request_id, candidate_text=content,
    )
    db.add(row)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        # 唯一约束兜底并发：同一 request_id 已被并发请求写入，按重放成功处理
        if db.query(InterviewReverseQuestion).filter_by(
                interview_id=interview.id, request_id=request_id).first():
            return _reverse_state(interview, db)
        raise HTTPException(409, "反问提交冲突，请稍后重试")
    logger.info("interview=%s 反问第 %s 条已记录", interview.id, seq)
    return _reverse_state(interview, db)


def skip_reverse_core(db: Session, interview: Interview, user: User) -> Dict[str, Any]:
    """跳过反问环节，允许直接结算。"""
    if interview.user_id != user.id:
        raise HTTPException(403, "无权操作此面试")
    db.refresh(interview)
    if (interview.phase or "QA") != "REVERSE":
        raise HTTPException(409, "当前不在反问环节")
    interview.phase = "DONE"
    db.commit()
    return _reverse_state(interview, db)


def aggregate_scores(questions):
    """按题目难度加权，追问同属其实际技能，排除跳过项的能力证据。"""
    items = [(q, q.answer.evaluation) for q in questions if q.answer and q.answer.evaluation]
    weights = {"EASY": 1.0, "MEDIUM": 1.2, "HARD": 1.5}
    total_weight = sum(weights.get(q.difficulty, 1.2) for q, _ in items)
    total = round(sum(e.total_score * weights.get(q.difficulty, 1.2) for q, e in items) / total_weight, 1)
    dimension_keys = {"专业基础": "professional", "相关性": "relevance", "完整性": "completeness",
                      "逻辑结构": "logic", "实践深度": "depth", "沟通表达": "communication"}
    dimensions = {label: round(sum(json.loads(e.dimensions_json).get(key, 0) * weights.get(q.difficulty, 1.2)
                                  for q, e in items) / total_weight, 1) for label, key in dimension_keys.items()}
    by_skill = {}
    for q, e in items:
        source = json.loads(e.provenance_json or "{}").get("source", "UNKNOWN")
        if source not in ("REAL", "RULE") or not (q.answer.text or "").strip():
            continue
        by_skill.setdefault(q.skill_name, []).append((q, e, weights.get(q.difficulty, 1.2)))
    return total, dimensions, by_skill


async def finalize_interview(db: Session, interview: Interview, user: User, force: bool = False) -> InterviewReport:
    if interview.user_id != user.id:
        raise HTTPException(403, "无权生成此面试报告")
    db.refresh(interview)
    rep = db.query(InterviewReport).filter_by(interview_id=interview.id).first()
    if rep and interview.learning_state in ("COMPLETED", "UNKNOWN"):
        return rep
    if interview.status in ("CANCELLED", "EXPIRED"):
        raise HTTPException(409, "面试已中止或过期，无法结算")
    evaluations = db.query(AnswerEvaluation).filter_by(interview_id=interview.id).all()
    if not evaluations:
        raise HTTPException(409, "尚无评分记录，无法生成报告")
    if not force and len(evaluations) < interview.total_questions:
        raise HTTPException(409, "还有题目未作答")
    lease = uuid.uuid4().hex
    claimed = db.query(Interview).filter(Interview.id == interview.id, _lease_available()).update(
        {"processing_token": lease, "processing_started_at": datetime.utcnow(),
         "report_state": "PROCESSING" if not rep else "COMPLETED"}, synchronize_session=False)
    if not claimed:
        db.rollback()
        raise HTTPException(409, "报告或答案正在处理，请稍后重试")
    db.commit()
    try:
        jd_text, _ = load_interview_context(interview, db)
        if not rep:
            db.expire_all()
            questions = db.query(InterviewQuestion).filter_by(interview_id=interview.id).order_by(InterviewQuestion.seq).all()
            total, dimensions, by_skill = aggregate_scores(questions)
            qa_pairs = [{"seq": q.seq, "question": q.text, "answer": q.answer.text,
                         "score": q.answer.evaluation.total_score} for q in questions if q.answer and q.answer.evaluation]
            with ai_context(user.id, interview.id, "report-" + lease):
                report_data = await ai_provider.generate_report(interview.id, interview.total_questions,
                    [e.total_score for e in evaluations], qa_pairs=qa_pairs, job_title=interview.job.title if interview.job else "综合岗位")
            provenance = report_data.get("_ai_meta", {"source": "UNKNOWN"})
            if interview.type == "ENTERPRISE_RECRUITMENT" and provenance.get("source") != "REAL":
                raise HTTPException(503, "正式面试的报告生成暂不可用，请稍后重试")
            provenance["score_source"] = "WEIGHTED_ANSWER_EVALUATIONS"
            provenance["answer_sources"] = sorted({json.loads(e.provenance_json or "{}").get("source", "UNKNOWN") for e in evaluations})
            provenance["difficulty_weights"] = {"EASY": 1, "MEDIUM": 1.2, "HARD": 1.5}
            db.expire_all()
            locked = db.query(Interview).filter_by(id=interview.id, processing_token=lease).update(
                {"processing_started_at": datetime.utcnow()}, synchronize_session=False)
            if not locked:
                raise HTTPException(409, "报告处理租约已变化，请重试")
            # 反问环节汇总：进报告素材，不进总分（避免变相惩罚内向型候选人）
            reverse_state = _reverse_state(interview, db)
            reverse_summary = {
                "questions": reverse_state["questions"],
                "question_count": reverse_state["used_count"],
                "skipped": reverse_state["used_count"] == 0,
                "comment": (
                    f"反问环节不评分、不耗时，本场记录了你提出的 {reverse_state['used_count']} 个问题，"
                    "可原样带到真实面试现场使用。"
                    if reverse_state["used_count"] else
                    "本次未使用反问环节。真实面试中反问是展示你对岗位动机与思考深度的窗口，"
                    "建议准备 2~3 个与业务、团队或成长相关的问题。"
                ),
            }
            rep = InterviewReport(interview_id=interview.id, user_id=user.id, total_score=total,
                performance_level="优秀" if total >= 85 else "表现良好" if total >= 70 else "待提升",
                dimension_scores_json=json.dumps(dimensions, ensure_ascii=False),
                strengths_json=json.dumps(report_data["strengths"], ensure_ascii=False),
                weaknesses_json=json.dumps(report_data["weaknesses"], ensure_ascii=False),
                suggestions_json=json.dumps(report_data["suggestions"], ensure_ascii=False), summary=report_data["summary"],
                provenance_json=json.dumps(provenance, ensure_ascii=False),
                reverse_summary_json=json.dumps(reverse_summary, ensure_ascii=False), status="COMPLETED")
            db.add(rep)
            for skill, evidence in by_skill.items():
                weight = sum(w for _, _, w in evidence)
                score = round(sum(e.total_score * w for _, e, w in evidence) / weight, 1)
                db.add(CompetencyHistory(user_id=user.id, competency_name=skill, score=score,
                    source_type="INTERVIEW", source_id=interview.id,
                    evidence_json=json.dumps({"question_ids": [q.id for q, _, _ in evidence],
                                              "evaluation_ids": [e.id for _, e, _ in evidence],
                                              "sample_count": len(evidence), "rubric_version": RUBRIC_VERSION})))
                comp = db.query(UserCompetency).filter_by(user_id=user.id, competency_name=skill).first()
                if not comp:
                    comp = UserCompetency(user_id=user.id, competency_name=skill)
                    db.add(comp)
                comp.score, comp.confidence = score, round(min(.95, len(evidence) / 5), 2)
            db.refresh(interview)
            interview.status, interview.report_state = "COMPLETED", "COMPLETED"
            # 结算即环节收尾：反问未走完（提前交卷）时也标记为 DONE，避免留下悬挂状态
            interview.phase = "DONE"
            interview.ended_at = interview.ended_at or datetime.utcnow()
            interview.version += 1
            db.commit()
        # 学习路线是独立可恢复步骤：不删除已完成任务，不重复评分或能力证据。
        db.query(Interview).filter_by(id=interview.id, processing_token=lease).update({"learning_state": "PROCESSING"})
        db.commit()
        await generate_and_store_learning_plan(db, user, resolve_target_job(user), jd_text=jd_text or None,
                                               gaps=json.loads(rep.weaknesses_json), replace=False)
        db.query(Interview).filter_by(id=interview.id, processing_token=lease).update(
            {"learning_state": "COMPLETED", "processing_token": None, "processing_started_at": None})
        db.commit()
        return rep
    except Exception:
        db.rollback()
        has_report = db.query(InterviewReport).filter_by(interview_id=interview.id).first()
        db.query(Interview).filter_by(id=interview.id, processing_token=lease).update(
            {"report_state": "COMPLETED" if has_report else "FAILED",
             "learning_state": "FAILED" if has_report else "PENDING",
             "processing_token": None, "processing_started_at": None}, synchronize_session=False)
        db.commit()
        if has_report:
            logger.exception("学习路线生成失败，报告已保存，可重试学习步骤")
            return has_report
        raise
