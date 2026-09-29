import json
import random
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import require_auth, log_operation
from app.core import state_machine
from app.models.user import User
from app.models.job import Job
from app.models.interview import (
    Interview, InterviewPlan, InterviewQuestion, InterviewAnswer,
    AnswerEvaluation, InterviewReport
)
from app.models.resume import Resume
from app.models.question import QuestionBank
from app.services.paper_builder import (
    build_paper, paper_from_bank_ids, collect_job_skills, allocate_counts, resolve_ratio,
    PROFESSIONAL, GENERAL, STRESS, Paper
)
from app.services.interview_core import (
    build_jd_text, build_resume_context, load_interview_context,
    build_ai_reference_points, get_remaining_seconds, mark_question_shown,
    submit_answer_core, finalize_interview
)
from app.schemas.common import ResponseModel
from app.schemas.interview import (
    InterviewCreate, InterviewOut, InterviewQuestionOut,
    InterviewAnswerRequest, AnswerEvaluationOut, InterviewReportOut,
    PaperPreviewOut, PaperPreviewItem
)
from app.ai.provider import ai_provider

router = APIRouter(tags=["AI 模拟面试与复盘"])

# 题库为空（未灌库）时的兜底题，保证面试流程不中断
FALLBACK_QUESTIONS = [
    {"text": "请介绍一个你深度参与的项目，说明你负责的核心模块、遇到的最大技术难点以及最终的解决思路与量化收益。",
     "question_type": "GENERAL", "skill_name": "项目经验", "stage": "项目深挖", "difficulty": "MEDIUM", "time_limit_sec": 240},
    {"text": "在高并发场景下，你如何保障缓存与数据库的一致性？请说明至少两种方案的适用边界与取舍。",
     "question_type": "PROFESSIONAL", "skill_name": "Redis", "stage": "专业基础", "difficulty": "MEDIUM", "time_limit_sec": 180},
    {"text": "请说明一次线上故障的完整处置过程：发现问题后的第一步是什么，如何定位根因，事后做了哪些机制性改进？",
     "question_type": "STRESS", "skill_name": "抗压能力", "stage": "压力应对", "difficulty": "HARD", "time_limit_sec": 150},
    {"text": "你如何设计一个接口的幂等机制？请给出至少两种不同强度的方案，并说明各自的适用场景。",
     "question_type": "PROFESSIONAL", "skill_name": "后端设计", "stage": "深度探究", "difficulty": "MEDIUM", "time_limit_sec": 180},
    {"text": "谈谈你对所在岗位未来两年能力要求的理解，以及你计划如何补齐自身与要求之间的差距。",
     "question_type": "GENERAL", "skill_name": "综合素养", "stage": "综合素养", "difficulty": "EASY", "time_limit_sec": 150},
]


def next_fallback_question(used_texts: List[str], total: int, seq: int) -> dict:
    """题库为空时的兜底组卷：优先取未使用过的题目，用尽后按序号生成变体。"""
    pool = [q for q in FALLBACK_QUESTIONS if q["text"] not in (used_texts or [])]
    if pool:
        picked = random.choice(pool)
    else:
        base = FALLBACK_QUESTIONS[(seq - 1) % len(FALLBACK_QUESTIONS)]
        picked = dict(base)
    return dict(picked)


def question_to_out(q: InterviewQuestion, reveal_reference: bool = False) -> InterviewQuestionOut:
    """题目序列化。

    作答过程中不下发参考答案要点（reveal_reference=False），避免开卷作答；
    面试结束（COMPLETED/CANCELLED）后的复盘阶段才下发。
    """
    points: List[str] = []
    if reveal_reference and q.reference_points_json:
        try:
            parsed = json.loads(q.reference_points_json)
            points = parsed if isinstance(parsed, list) else []
        except Exception:
            points = []
    return InterviewQuestionOut(
        id=q.id,
        seq=q.seq,
        stage=q.stage,
        question_type=q.question_type or PROFESSIONAL,
        skill_name=q.skill_name,
        text=q.text,
        difficulty=q.difficulty,
        hints=q.hints,
        time_limit_sec=q.time_limit_sec or 180,
        source=q.source or "QUESTION_BANK",
        reference_points=points,
        reveal_reference=reveal_reference,
        user_answer=q.answer.text if q.answer else None,
        evaluation=None
    )


def build_question_payload(q: InterviewQuestion, reveal_reference: bool = False) -> dict:
    """供 WebSocket 通道使用的题目字典（与 REST 下发字段保持一致）。"""
    points: List[str] = []
    if reveal_reference and q.reference_points_json:
        try:
            parsed = json.loads(q.reference_points_json)
            points = parsed if isinstance(parsed, list) else []
        except Exception:
            points = []
    return {
        "question_id": q.id,
        "id": q.id,
        "seq": q.seq,
        "text": q.text,
        "stage": q.stage,
        "question_type": q.question_type or PROFESSIONAL,
        "skill_name": q.skill_name,
        "difficulty": q.difficulty,
        "hints": q.hints,
        "time_limit_sec": q.time_limit_sec or 180,
        "source": q.source or "QUESTION_BANK",
        "reference_points": points,
    }


def build_interview_out(interview: Interview) -> InterviewOut:
    # 仅面试结束后下发参考答案，作答过程中保持"闭卷"
    reveal = interview.status in ("COMPLETED", "CANCELLED", "EXPIRED")
    q_outs = []
    curr_q_out = None
    for q in sorted(interview.questions, key=lambda x: x.seq):
        q_item = question_to_out(q, reveal_reference=reveal)
        if q.answer and q.answer.evaluation:
            e = q.answer.evaluation
            q_item.evaluation = {
                "score": e.total_score,
                "dimensions": json.loads(e.dimensions_json) if e.dimensions_json else {},
                "evidence": json.loads(e.evidence_json) if e.evidence_json else [],
                "weaknesses": json.loads(e.weaknesses_json) if e.weaknesses_json else [],
                "suggestions": json.loads(e.suggestions_json) if e.suggestions_json else [],
                "next_action": e.next_action
            }
        q_outs.append(q_item)
        if q.seq == interview.current_question_seq:
            curr_q_out = q_item

    job_title = "Java后端开发工程师"
    if interview.job:
        job_title = interview.job.title

    return InterviewOut(
        id=interview.id,
        user_id=interview.user_id,
        company_id=interview.company_id,
        job_id=interview.job_id,
        job_title=job_title,
        application_id=interview.application_id,
        type=interview.type,
        mode=interview.mode,
        difficulty=interview.difficulty,
        status=interview.status,
        current_question_seq=interview.current_question_seq,
        total_questions=interview.total_questions,
        duration_minutes=interview.duration_minutes,
        started_at=interview.started_at,
        ended_at=interview.ended_at,
        created_at=interview.created_at,
        remaining_seconds=get_remaining_seconds(interview),
        answered_count=sum(1 for q in interview.questions if q.answer and q.answer.evaluation),
        questions=q_outs,
        current_question=curr_q_out
    )


@router.get("/interviews/paper-ratio", response_model=ResponseModel[dict])
def get_paper_ratio(mode: str = "COMPREHENSIVE", total_questions: int = 5,
                    db: Session = Depends(get_db)):
    """查询某面试模式的题型配比与题量分配（前端用于展示"5:3:2"说明）。"""
    bank_total = db.query(QuestionBank).filter(QuestionBank.enabled == True).count()  # noqa: E712
    ratio = dict(zip(["PROFESSIONAL", "GENERAL", "STRESS"], resolve_ratio(mode)))
    return ResponseModel(data={
        "mode": (mode or "COMPREHENSIVE").upper(),
        "total_questions": max(1, int(total_questions or 1)),
        "ratio": ratio,
        "allocated": allocate_counts(mode, total_questions),
        "bank_available": bank_total,
        "bank_ready": bank_total > 0,
    })


@router.post("/interviews/paper-preview", response_model=ResponseModel[PaperPreviewOut])
async def preview_paper(req: InterviewCreate, current_user: User = Depends(require_auth),
                        db: Session = Depends(get_db)):
    """组卷预览：不落库，返回将要抽到的题目（含参考答案，供用户确认考卷）。"""
    job = db.query(Job).filter(Job.id == req.job_id).first() if req.job_id else None
    bank_total = db.query(QuestionBank).filter(QuestionBank.enabled == True).count()  # noqa: E712

    if not req.use_question_bank or bank_total == 0:
        return ResponseModel(data=PaperPreviewOut(
            mode=(req.mode or "COMPREHENSIVE").upper(),
            total_questions=req.total_questions,
            ratio=dict(zip(["PROFESSIONAL", "GENERAL", "STRESS"], resolve_ratio(req.mode))),
            allocated=allocate_counts(req.mode, req.total_questions),
            from_bank=0,
            missing_for_ai={},
            matched_category=(job.category if job else "通用"),
            job_skills=collect_job_skills(job),
            bank_available=bank_total,
            questions=[]
        ))

    paper = build_paper(db, job, req.mode, req.difficulty, req.total_questions, count_usage=False)
    return ResponseModel(data=PaperPreviewOut(
        mode=paper.plan["mode"],
        total_questions=req.total_questions,
        ratio=paper.plan["ratio"],
        allocated=paper.plan["allocated"],
        from_bank=paper.plan["from_bank"],
        missing_for_ai=paper.missing,
        matched_category=paper.plan["matched_category"],
        job_skills=paper.plan["job_skills"],
        bank_available=paper.plan["bank_total"],
        questions=[
            PaperPreviewItem(
                seq=s.seq, bank_id=s.bank_id, question_type=s.question_type,
                skill_name=s.skill_name, stage=s.stage, difficulty=s.difficulty,
                text=s.text, time_limit_sec=s.time_limit_sec, source=s.source
            ) for s in paper.slots
        ]
    ))


@router.get("/interviews/bank-stats", response_model=ResponseModel[dict])
def get_bank_stats(current_user: User = Depends(require_auth), db: Session = Depends(get_db)):
    """题库统计：按题型与岗位大类分布，用于前端展示题库覆盖情况。"""
    rows = db.query(QuestionBank).filter(QuestionBank.enabled == True).all()  # noqa: E712
    by_type: dict = {}
    by_category: dict = {}
    for r in rows:
        by_type[r.question_type] = by_type.get(r.question_type, 0) + 1
        by_category[r.job_category] = by_category.get(r.job_category, 0) + 1
    return ResponseModel(data={
        "total": len(rows),
        "by_type": by_type,
        "by_category": by_category,
        "ready": len(rows) > 0,
    })


@router.post("/interviews", response_model=ResponseModel[InterviewOut])
async def create_interview(req: InterviewCreate, current_user: User = Depends(require_auth), db: Session = Depends(get_db)):
    job_title = "Java后端开发工程师"
    job = None
    if req.job_id:
        job = db.query(Job).filter(Job.id == req.job_id).first()
        if job:
            job_title = job.title

    # 若未显式传入 JD 文本，则从所选岗位自动带出
    jd_text = build_jd_text(job, req.jd_text)

    # 加载用户选择的简历（用于个性化出题）
    resume = None
    if req.resume_id:
        resume = db.query(Resume).filter(
            Resume.id == req.resume_id,
            Resume.user_id == current_user.id
        ).first()
    if not resume:
        resume = db.query(Resume).filter(
            Resume.user_id == current_user.id,
            Resume.is_deleted == False
        ).order_by(Resume.is_default.desc(), Resume.id.desc()).first()
    resume_context = build_resume_context(resume)

    # Create interview record
    interview = Interview(
        user_id=current_user.id,
        company_id=None,
        job_id=req.job_id,
        resume_id=resume.id if resume else None,
        jd_text=jd_text or None,
        application_id=req.application_id,
        type=req.type,
        mode=req.mode,
        difficulty=req.difficulty,
        status="READY",
        current_question_seq=1,
        total_questions=req.total_questions,
        duration_minutes=req.duration_minutes,
        purpose=(req.purpose or "NORMAL").upper(),
        derived_from_id=req.derived_from_id,
        privacy_scope="PRIVATE" if req.type == "PERSONAL_TRAINING" else "COMPANY_AUTHORIZED"
    )
    db.add(interview)
    db.commit()
    db.refresh(interview)

    # ========== 组卷：优先结构化题库，缺口由 AI 补足 ==========
    bank_total = db.query(QuestionBank).filter(QuestionBank.enabled == True).count()  # noqa: E712
    paper = None
    if req.use_question_bank and bank_total > 0:
        if req.selected_bank_ids:
            # 用户已在预览中确认考卷：按给定题库 ID 出题，保证"所见即所考"
            chosen = paper_from_bank_ids(db, req.selected_bank_ids[:req.total_questions])
            # 自动组卷仅用于补足名额，不计次（避免计到未实际使用的题上）
            auto = build_paper(db, job, req.mode, req.difficulty, req.total_questions, count_usage=False)
            slots = chosen + auto.slots[:max(0, req.total_questions - len(chosen))]
            for i, s in enumerate(slots, start=1):
                s.seq = i
            paper = Paper(slots=slots, missing={}, plan=auto.plan)
            paper.plan["from_bank"] = len(slots)
            paper.plan["bank_ids"] = [s.bank_id for s in slots]
            paper.plan["user_selected_paper"] = True
            # 计次只算最终真正入卷的题目
            final_ids = [s.bank_id for s in slots if s.bank_id]
            if final_ids:
                db.query(QuestionBank).filter(QuestionBank.id.in_(final_ids)).update(
                    {QuestionBank.usage_count: QuestionBank.usage_count + 1}, synchronize_session=False
                )
        else:
            paper = build_paper(db, job, req.mode, req.difficulty, req.total_questions)

    if paper and paper.slots:
        for slot in paper.slots:
            db.add(InterviewQuestion(interview_id=interview.id, **slot.to_interview_question_kwargs()))
        # 题库缺口：按题型走 AI 兜底生成
        missing_total = sum(paper.missing.values()) if paper.missing else 0
        start_seq = len(paper.slots)
        for i in range(missing_total):
            q_data = await ai_provider.generate_question(
                job_title=job_title, seq=start_seq + i + 1, difficulty=req.difficulty,
                jd_text=jd_text, resume_context=resume_context
            )
            db.add(InterviewQuestion(
                interview_id=interview.id,
                seq=start_seq + i + 1,
                stage=q_data.get("stage") or "专业基础",
                question_type=PROFESSIONAL,
                skill_name=q_data.get("skill_name") or job_title,
                text=q_data.get("question") or "",
                difficulty=q_data.get("difficulty") or req.difficulty,
                hints=q_data.get("hints"),
                time_limit_sec=180,
                reference_points_json=json.dumps(
                    build_ai_reference_points(job_title, q_data.get("question") or ""),
                    ensure_ascii=False
                ),
                source="AI_GENERATED"
            ))
        stages = [{"stage": s.stage, "skill_name": s.skill_name, "question_type": s.question_type,
                   "bank_id": s.bank_id, "seq": s.seq} for s in paper.slots]
        plan = InterviewPlan(
            interview_id=interview.id,
            stages_json=json.dumps(stages, ensure_ascii=False),
            paper_json=paper.snapshot_json,
            total_questions=req.total_questions,
            duration_minutes=req.duration_minutes
        )
        db.add(plan)
        db.commit()
    else:
        # 未启用题库或题库为空：回退"逐题动态生成"模式（题库缺失时保证流程可用）
        used_texts: List[str] = []
        for seq in range(1, req.total_questions + 1):
            q_data = await ai_provider.generate_question(
                job_title=job_title,
                seq=seq,
                difficulty=req.difficulty,
                last_question=used_texts[-1] if used_texts else None,
                jd_text=jd_text,
                resume_context=resume_context
            )
            text = q_data.get("question") or ""
            if not text:
                fb = next_fallback_question(used_texts, req.total_questions, seq)
                text = fb["text"]
                q_data = {**fb, "question": text}
            used_texts.append(text)
            db.add(InterviewQuestion(
                interview_id=interview.id,
                seq=seq,
                stage=q_data.get("stage") or "专业基础",
                question_type=q_data.get("question_type") or PROFESSIONAL,
                skill_name=q_data.get("skill_name") or job_title,
                text=text,
                difficulty=q_data.get("difficulty") or req.difficulty,
                hints=q_data.get("hints"),
                time_limit_sec=q_data.get("time_limit_sec") or 180,
                reference_points_json=json.dumps(
                    build_ai_reference_points(job_title, text), ensure_ascii=False
                ),
                source="AI_GENERATED"
            ))
        stages = [
            {"stage": "专业基础", "questions_count": 2},
            {"stage": "深度探究", "questions_count": 1},
            {"stage": "项目深挖", "questions_count": 1},
            {"stage": "系统设计", "questions_count": 1}
        ]
        plan = InterviewPlan(
            interview_id=interview.id,
            stages_json=json.dumps(stages, ensure_ascii=False),
            paper_json=json.dumps({"mode": (req.mode or "COMPREHENSIVE").upper(),
                                   "from_bank": 0,
                                   "reason": "question_bank_disabled_or_empty",
                                   "ratio": dict(zip(["PROFESSIONAL", "GENERAL", "STRESS"], resolve_ratio(req.mode))),
                                   "allocated": allocate_counts(req.mode, req.total_questions)},
                                  ensure_ascii=False),
            total_questions=req.total_questions,
            duration_minutes=req.duration_minutes
        )
        db.add(plan)
        db.commit()

    db.refresh(interview)
    # 卷面已就绪：记录首题呈现时间，作为服务端单题计时锚点
    mark_question_shown(interview)
    db.commit()

    source_desc = "题库组卷" if (paper and paper.slots) else "AI 动态生成"
    log_operation(db, current_user.id, current_user.email, "PERSONAL", "CREATE_INTERVIEW",
                  "INTERVIEW", interview.id,
                  f"创建面试仓会话【{req.mode}｜{source_desc}｜{req.total_questions}题】")

    return ResponseModel(data=build_interview_out(interview))

@router.get("/interviews", response_model=ResponseModel[List[dict]])
def list_interviews(current_user: User = Depends(require_auth), db: Session = Depends(get_db)):
    interviews = db.query(Interview).filter(Interview.user_id == current_user.id).order_by(Interview.id.desc()).all()
    results = []
    for i in interviews:
        # 无报告不再兜底写死 82 分：未出报告就是 None，前端显示"未结算"
        score = i.report.total_score if i.report else None
        results.append({
            "id": i.id,
            "job_title": i.job.title if i.job else "Java后端开发工程师",
            "type": i.type,
            "mode": i.mode,
            "difficulty": i.difficulty,
            "status": i.status,
            "total_questions": i.total_questions,
            "duration_minutes": i.duration_minutes,
            "score": score,
            "purpose": i.purpose or "NORMAL",
            "has_report": bool(i.report),
            "created_at": i.created_at.strftime("%Y-%m-%d %H:%M")
        })
    return ResponseModel(data=results)


@router.get("/interviews/history-comparison", response_model=ResponseModel[dict])
def get_history_comparison(job_id: Optional[int] = None, include_retrain: bool = False,
                           current_user: User = Depends(require_auth), db: Session = Depends(get_db)):
    """同一岗位多次面试的逐维对比与进步幅度。

    - 默认排除 purpose=RETRAIN 的重练记录，避免重练拉高/扰动成长趋势；
    - 至少 2 次有效面试才给出 delta 与维度对比，否则返回空态（不做写死兜底）；
    - 对比口径：同 job_id（未传则用用户目标岗位最近一次面试的 job_id）；无 job_id 的面试不参与同岗位对比。
    """
    q = db.query(Interview).filter(
        Interview.user_id == current_user.id,
        Interview.status == "COMPLETED"
    )
    if not include_retrain:
        q = q.filter(or_(Interview.purpose.is_(None), Interview.purpose != "RETRAIN"))
    interviews = q.order_by(Interview.id.asc()).all()

    target_job_id = job_id
    if not target_job_id:
        # 未指定岗位时，取用户最近一次有岗位的真实面试作为对比基准
        for iv in reversed(interviews):
            if iv.job_id:
                target_job_id = iv.job_id
                break

    if not target_job_id:
        return ResponseModel(data={
            "job_id": None, "job_title": None, "sessions": [],
            "dimension_trends": {}, "ready": False,
            "message": "暂无可对比的同岗位面试记录"
        })

    reports = (db.query(InterviewReport)
               .join(Interview, InterviewReport.interview_id == Interview.id)
               .filter(Interview.user_id == current_user.id,
                       Interview.job_id == target_job_id)
               .order_by(InterviewReport.id.asc()).all())
    if not include_retrain:
        reports = [r for r in reports if (r.interview.purpose or "NORMAL") != "RETRAIN"]

    if len(reports) < 2:
        job = db.query(Job).filter(Job.id == target_job_id).first()
        return ResponseModel(data={
            "job_id": target_job_id,
            "job_title": job.title if job else None,
            "sessions": [{
                "interview_id": r.interview_id,
                "score": r.total_score,
                "mode": r.interview.mode if r.interview else None,
                "created_at": r.created_at.strftime("%Y-%m-%d"),
            } for r in reports],
            "dimension_trends": {}, "ready": False,
            "message": "同岗位至少需要 2 次完成的面试才能生成对比"
        })

    sessions, dim_series = [], {}
    for idx, r in enumerate(reports, start=1):
        sessions.append({
            "seq": idx,
            "interview_id": r.interview_id,
            "score": r.total_score,
            "mode": r.interview.mode if r.interview else None,
            "difficulty": r.interview.difficulty if r.interview else None,
            "total_questions": r.interview.total_questions if r.interview else None,
            "created_at": r.created_at.strftime("%Y-%m-%d"),
        })
        try:
            dims = json.loads(r.dimension_scores_json) or {}
        except Exception:
            dims = {}
        for k, v in dims.items():
            dim_series.setdefault(k, []).append(v)

    dimension_trends = {}
    for k, vals in dim_series.items():
        first, last = vals[0], vals[-1]
        dimension_trends[k] = {
            "series": [round(v, 1) for v in vals],
            "delta": round(last - first, 1),
            "improved": last > first,
        }

    job = db.query(Job).filter(Job.id == target_job_id).first()
    total_delta = round(sessions[-1]["score"] - sessions[0]["score"], 1)
    return ResponseModel(data={
        "job_id": target_job_id,
        "job_title": job.title if job else None,
        "sessions": sessions,
        "dimension_trends": dimension_trends,
        "total_delta": total_delta,
        "session_count": len(sessions),
        "ready": True,
        "include_retrain": include_retrain,
    })


@router.get("/interviews/weak-questions", response_model=ResponseModel[dict])
def get_weak_questions(threshold: float = 60.0, limit: int = 10,
                       current_user: User = Depends(require_auth), db: Session = Depends(get_db)):
    """我的薄弱题清单：按题库题目（bank_id）聚合历次作答得分。

    口径：同一 bank_id 取「最近一次得分」判定薄弱（比最低分更符合"现在还不行"的语义），
    同时返回历史作答次数与最高/最低分供参考；仅统计已完成面试中的题目。
    """
    rows = (db.query(InterviewQuestion, AnswerEvaluation, Interview)
            .join(InterviewAnswer, InterviewAnswer.question_id == InterviewQuestion.id)
            .join(AnswerEvaluation, AnswerEvaluation.answer_id == InterviewAnswer.id)
            .join(Interview, Interview.id == InterviewQuestion.interview_id)
            .filter(Interview.user_id == current_user.id,
                    Interview.status == "COMPLETED",
                    InterviewQuestion.bank_id.isnot(None))
            .order_by(InterviewQuestion.id.asc()).all())

    grouped: dict = {}
    for q, ev, iv in rows:
        g = grouped.setdefault(q.bank_id, {
            "bank_id": q.bank_id, "skill_name": q.skill_name,
            "question_type": q.question_type, "difficulty": q.difficulty,
            "text": q.text, "scores": [], "attempts": 0,
            "last_interview_id": iv.id,
        })
        g["scores"].append(ev.total_score)
        g["attempts"] += 1
        g["last_interview_id"] = iv.id

    weak = []
    for g in grouped.values():
        latest = g["scores"][-1]
        if latest < threshold:
            weak.append({
                "bank_id": g["bank_id"],
                "skill_name": g["skill_name"],
                "question_type": g["question_type"],
                "difficulty": g["difficulty"],
                "text": g["text"],
                "attempts": g["attempts"],
                "latest_score": round(latest, 1),
                "best_score": round(max(g["scores"]), 1),
                "worst_score": round(min(g["scores"]), 1),
                "last_interview_id": g["last_interview_id"],
            })
    # 最近得分低者优先，其次作答次数多者优先
    weak.sort(key=lambda x: (x["latest_score"], -x["attempts"]))
    weak = weak[:max(1, min(limit, 50))]

    # 校验题目仍在题库中且启用（被停用的题不应再推荐重练）
    bank_ids = [w["bank_id"] for w in weak]
    available = set()
    if bank_ids:
        for qb in db.query(QuestionBank).filter(
            QuestionBank.id.in_(bank_ids),
            QuestionBank.enabled == True  # noqa: E712
        ).all():
            available.add(qb.id)
    retrainable = [w for w in weak if w["bank_id"] in available]

    return ResponseModel(data={
        "threshold": threshold,
        "total_attempted_bank_questions": len(grouped),
        "weak_count": len(retrainable),
        "items": retrainable,
        "retrain_bank_ids": [w["bank_id"] for w in retrainable],
    })


@router.get("/interviews/{id}", response_model=ResponseModel[InterviewOut])
def get_interview(id: int, current_user: User = Depends(require_auth), db: Session = Depends(get_db)):
    interview = db.query(Interview).filter(Interview.id == id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="面试不存在")

    # SEC-06 Check: Private personal training is strictly prohibited for enterprises
    if interview.user_id != current_user.id:
        if interview.type == "PERSONAL_TRAINING":
            raise HTTPException(status_code=403, detail="【SEC-06 越权防护】私人训练面试默认仅本人可见，企业无权访问")
        # For enterprise recruitment, check if user belongs to this company
        user_roles = [r.role_code for r in current_user.roles]
        if "SUPER_ADMIN" not in user_roles:
            is_company = any(r.company_id == interview.company_id for r in current_user.roles if r.company_id)
            if not is_company:
                raise HTTPException(status_code=403, detail="无权访问该面试记录")

    return ResponseModel(data=build_interview_out(interview))

@router.post("/interviews/{id}/start", response_model=ResponseModel[dict])
def start_interview(id: int, current_user: User = Depends(require_auth), db: Session = Depends(get_db)):
    interview = db.query(Interview).filter(Interview.id == id, Interview.user_id == current_user.id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="面试不存在")

    state_machine.ensure(interview.status, state_machine.CAN_START, "开始面试")
    interview.status = "IN_PROGRESS"
    if not interview.started_at:
        interview.started_at = datetime.utcnow()
    if not interview.current_question_shown_at:
        mark_question_shown(interview)
    db.commit()
    return ResponseModel(data={
        "status": interview.status,
        "remaining_seconds": get_remaining_seconds(interview),
        "message": "面试开始"
    })

@router.post("/interviews/{id}/pause", response_model=ResponseModel[dict])
def pause_interview(id: int, current_user: User = Depends(require_auth), db: Session = Depends(get_db)):
    interview = db.query(Interview).filter(Interview.id == id, Interview.user_id == current_user.id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="面试不存在")

    state_machine.ensure(interview.status, state_machine.CAN_PAUSE, "暂停面试")
    interview.status = "PAUSED"
    interview.paused_at = datetime.utcnow()
    db.commit()
    return ResponseModel(data={"status": "PAUSED", "message": "面试已暂停"})

@router.post("/interviews/{id}/resume", response_model=ResponseModel[dict])
def resume_interview(id: int, current_user: User = Depends(require_auth), db: Session = Depends(get_db)):
    interview = db.query(Interview).filter(Interview.id == id, Interview.user_id == current_user.id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="面试不存在")

    state_machine.ensure(interview.status, state_machine.CAN_RESUME, "继续面试")
    interview.status = "IN_PROGRESS"
    # 暂停时长不计入单题用时与整场用时：把锚点整体后移
    if interview.paused_at:
        gap = datetime.utcnow() - interview.paused_at
        if interview.current_question_shown_at:
            interview.current_question_shown_at += gap
        if interview.started_at:
            interview.started_at += gap
        interview.paused_at = None
    db.commit()
    return ResponseModel(data={
        "status": "IN_PROGRESS",
        "remaining_seconds": get_remaining_seconds(interview),
        "message": "面试已恢复继续"
    })

@router.post("/interviews/{id}/abort", response_model=ResponseModel[dict])
def abort_interview(id: int, current_user: User = Depends(require_auth), db: Session = Depends(get_db)):
    """中止面试：不生成报告，终态 CANCELLED，已答部分保留可查。"""
    interview = db.query(Interview).filter(Interview.id == id, Interview.user_id == current_user.id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="面试不存在")

    state_machine.ensure(interview.status, state_machine.CAN_ABORT, "中止面试")
    interview.status = "CANCELLED"
    interview.ended_at = datetime.utcnow()
    db.commit()
    log_operation(db, current_user.id, current_user.email, "PERSONAL", "ABORT_INTERVIEW",
                  "INTERVIEW", id, "中止模拟面试（未生成报告）")
    return ResponseModel(data={"status": "CANCELLED", "message": "面试已中止"})

@router.post("/interviews/{id}/answer", response_model=ResponseModel[AnswerEvaluationOut])
async def answer_interview_question(id: int, req: InterviewAnswerRequest, current_user: User = Depends(require_auth), db: Session = Depends(get_db)):
    interview = db.query(Interview).filter(Interview.id == id, Interview.user_id == current_user.id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="面试不存在")

    # 答题、评分、追问、推进统一走核心服务（与 WebSocket 通道共用）
    result = await submit_answer_core(
        db, interview, current_user,
        text=req.text, duration_sec=req.duration_sec
    )
    eval_res = result["eval_res"]
    next_q = result["next_question"]
    # 作答中不下发参考答案，保持闭卷
    next_q_out = question_to_out(next_q, reveal_reference=False) if next_q else None

    return ResponseModel(data=AnswerEvaluationOut(
        answer_id=result["answer"].id,
        total_score=eval_res["score"],
        dimensions=eval_res["dimensions"],
        evidence=eval_res["evidence"],
        weaknesses=eval_res["weaknesses"],
        missing_knowledge=eval_res["missing_knowledge"],
        suggestions=eval_res["suggestions"],
        next_action=eval_res.get("next_action", "CHANGE_TOPIC"),
        next_question=next_q_out,
        is_followup=result["is_followup"],
        is_finished=result["finished"],
        report_id=result.get("report_id"),
        remaining_seconds=result["remaining_seconds"],
        total_questions=interview.total_questions,
        raw_score=result.get("raw_score"),
        overtime=result.get("overtime", False),
        overtime_sec=result.get("overtime_sec", 0),
        is_empty=result.get("is_empty", False)
    ))

@router.post("/interviews/{id}/finish", response_model=ResponseModel[dict])
async def finish_interview(id: int, current_user: User = Depends(require_auth), db: Session = Depends(get_db)):
    interview = db.query(Interview).filter(Interview.id == id, Interview.user_id == current_user.id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="面试不存在")

    # 结算与报告生成统一走核心服务：幂等、未答完拦截、无作答不再产出假报告
    rep = await finalize_interview(db, interview, current_user, force=True)
    log_operation(db, current_user.id, current_user.email, "PERSONAL", "FINISH_INTERVIEW",
                  "INTERVIEW", id, f"完成模拟面试，得分：{rep.total_score}")

    return ResponseModel(data={
        "report_id": rep.id,
        "total_score": rep.total_score,
        "report_url": f"/personal/interviews/{id}/report"
    })

@router.get("/interviews/{id}/report", response_model=ResponseModel[InterviewReportOut])
def get_interview_report(id: int, current_user: User = Depends(require_auth), db: Session = Depends(get_db)):
    interview = db.query(Interview).filter(Interview.id == id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="面试记录不存在")

    # SEC-06 Check: Private personal training is strictly prohibited for enterprises
    if interview.user_id != current_user.id:
        if interview.type == "PERSONAL_TRAINING":
            raise HTTPException(status_code=403, detail="【SEC-06 越权防护】私人训练报告默认仅本人可见，企业无权访问")
        # If enterprise recruitment, verify user belongs to company
        user_roles = [r.role_code for r in current_user.roles]
        if "SUPER_ADMIN" not in user_roles:
            is_company = any(r.company_id == interview.company_id for r in current_user.roles if r.company_id)
            if not is_company:
                raise HTTPException(status_code=403, detail="无权访问该企业面试报告")

    report = interview.report
    if not report:
        # 不再返回写死的 82 分假报告：未结算就是未结算
        raise HTTPException(
            status_code=404,
            detail="本次面试尚未生成报告（未结算或已中止）"
        )

    # Questions breakdown
    q_analysis = []
    per_question_time = []
    for q in sorted(interview.questions, key=lambda x: x.seq):
        if q.answer and q.answer.evaluation:
            e = q.answer.evaluation
            try:
                ref_points = json.loads(q.reference_points_json) if q.reference_points_json else []
                if not isinstance(ref_points, list):
                    ref_points = []
            except Exception:
                ref_points = []
            limit = q.time_limit_sec or 180
            used = q.answer.duration_sec or 0
            is_ot = bool(q.answer.overtime) or used > limit
            ot_sec = q.answer.overtime_sec or (max(0, used - limit) if is_ot else 0)
            q_analysis.append({
                "seq": q.seq,
                "question": q.text,
                "answer": q.answer.text,
                "score": e.total_score,
                "question_type": q.question_type or PROFESSIONAL,
                "stage": q.stage,
                "skill_name": q.skill_name,
                "difficulty": q.difficulty,
                "source": q.source or "QUESTION_BANK",
                "reference_points": ref_points,
                "duration_sec": used,
                "time_limit_sec": limit,
                "overtime": is_ot,
                "overtime_sec": ot_sec,
                "is_empty": not (q.answer.text or "").strip(),
                "evidence": json.loads(e.evidence_json) if e.evidence_json else [],
                "weaknesses": json.loads(e.weaknesses_json) if e.weaknesses_json else [],
                "missing_knowledge": json.loads(e.missing_knowledge_json) if e.missing_knowledge_json else [],
                "suggestions": json.loads(e.suggestions_json) if e.suggestions_json else []
            })
            per_question_time.append({
                "seq": q.seq, "skill_name": q.skill_name,
                "duration_sec": used, "time_limit_sec": limit,
                "usage_ratio": round(used / limit, 2) if limit else 0,
                "overtime": is_ot, "overtime_sec": ot_sec,
            })

    # 时间维度汇总：用时分布与超时率（服务端口径）
    time_analysis = None
    if per_question_time:
        durs = [p["duration_sec"] for p in per_question_time]
        ot_items = [p for p in per_question_time if p["overtime"]]
        ratios = [p["usage_ratio"] for p in per_question_time]
        time_analysis = {
            "items": per_question_time,
            "total_answered": len(per_question_time),
            "total_time_sec": sum(durs),
            "avg_time_sec": round(sum(durs) / len(durs), 1),
            "max_time_sec": max(durs),
            "min_time_sec": min(durs),
            "overtime_count": len(ot_items),
            "overtime_rate": round(len(ot_items) / len(per_question_time), 2),
            "avg_usage_ratio": round(sum(ratios) / len(ratios), 2),
            "overtime_skills": sorted({p["skill_name"] for p in ot_items}),
        }

    return ResponseModel(data=InterviewReportOut(
        id=report.id,
        interview_id=report.interview_id,
        user_id=report.user_id,
        job_title=interview.job.title if interview.job else "Java后端开发工程师",
        interview_type="企业官方甄选面试" if interview.type == "ENTERPRISE_RECRUITMENT" else "AI 全真模拟与能力复盘",
        duration_minutes=interview.duration_minutes or 28,
        total_score=report.total_score,
        performance_level=report.performance_level,
        dimension_scores=json.loads(report.dimension_scores_json),
        strengths=json.loads(report.strengths_json),
        weaknesses=json.loads(report.weaknesses_json),
        suggestions=json.loads(report.suggestions_json),
        summary=report.summary,
        status=report.status,
        created_at=report.created_at,
        questions_analysis=q_analysis,
        time_analysis=time_analysis
    ))
