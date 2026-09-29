"""面试核心业务服务：REST 与 WebSocket 两条通道共用的答题、推进、结算逻辑。

抽取动机（修复 A 类问题）：
- 两通道此前各写一份答题/结算逻辑，出现 WS 重复创建 AnswerEvaluation、
  finish 通道 competency_name 写死 "Redis" 等分叉；
- next_action 自适应追问在整卷预生成后失效：现按评分建议从题库换/插追问题并后移卷面；
- 整场剩余时间以服务端 started_at 为准，前端刷新不再重置。
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.ai.provider import ai_provider
from app.core import state_machine
from app.models.interview import (
    Interview, InterviewAnswer, InterviewQuestion, AnswerEvaluation, InterviewReport
)
from app.models.job import Job
from app.models.profile import CompetencyHistory, UserCompetency
from app.models.question import QuestionBank
from app.models.resume import Resume
from app.models.user import User

logger = logging.getLogger("interview_service")

# 允许追问插入的次数上限（每场面试）
MAX_FOLLOWUP_INSERTS = 2

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


def get_remaining_seconds(interview: Interview) -> Optional[int]:
    """以服务端 started_at 为准的整场剩余秒数；未开始返回 None。"""
    if not interview.started_at:
        return None
    total = (interview.duration_minutes or 30) * 60
    elapsed = int((datetime.utcnow() - interview.started_at).total_seconds())
    return max(0, total - elapsed)


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
    db.commit()
    db.refresh(fu)
    db.refresh(interview)
    logger.info(f"interview={interview.id} 插入追问（{action}）bank_id={picked.id} seq={fu.seq}")
    return fu


async def submit_answer_core(
    db: Session, interview: Interview, user: User,
    text: str, duration_sec: Optional[int] = None
) -> Dict[str, Any]:
    """当前题作答 → 评分 → 落库 → （可能的追问）→ 推进下一题。REST/WS 共用。"""
    state_machine.ensure(interview.status, state_machine.ANSWERABLE, "提交作答")

    curr_q = db.query(InterviewQuestion).filter(
        InterviewQuestion.interview_id == interview.id,
        InterviewQuestion.seq == interview.current_question_seq
    ).first()
    if not curr_q:
        raise HTTPException(status_code=400, detail="未找到当前题目")

    # 重复提交拦截：当前题已有评分记录则拒绝（409），不再静默覆盖重评
    existing_answer = db.query(InterviewAnswer).filter(
        InterviewAnswer.question_id == curr_q.id).first()
    if existing_answer and existing_answer.evaluation is not None:
        raise HTTPException(
            status_code=409,
            detail=f"第 {curr_q.seq} 题已完成作答与评分，不能重复提交"
        )

    if interview.status == "READY":
        interview.status = "IN_PROGRESS"
        if not interview.started_at:
            interview.started_at = datetime.utcnow()
        if not interview.current_question_shown_at:
            mark_question_shown(interview)
        db.commit()

    # 服务端单题计时与超时判定（不信任客户端上报；无锚点时退回客户端值）
    real_duration, overtime_sec, is_overtime = measure_question_usage(
        interview, curr_q, duration_sec)
    duration_sec = real_duration

    answer = existing_answer
    if not answer:
        # 语音指标未接入真实分析：显式写 0（含义为"未测量"），不再沿用模型默认值 160/2 的假数据
        answer = InterviewAnswer(
            question_id=curr_q.id,
            interview_id=interview.id,
            user_id=user.id,
            text=text,
            duration_sec=duration_sec,
            speaking_rate=0,
            filler_count=0
        )
        db.add(answer)
        db.commit()
        db.refresh(answer)
    else:
        # 有答案但无评分（上次评分中断）：允许更新文本重评
        answer.text = text
        answer.duration_sec = duration_sec
        db.commit()

    answer.overtime = is_overtime
    answer.overtime_sec = overtime_sec
    db.commit()

    jd_text, resume_context = load_interview_context(interview, db)
    is_empty = not (text or "").strip()
    if is_empty:
        # 空作答：直接 0 分并明确提示，不消耗 LLM 调用
        eval_res = empty_answer_evaluation(curr_q.text)
    else:
        eval_res = await ai_provider.evaluate_answer(
            curr_q.text, text, curr_q.seq,
            jd_text=jd_text or None,
            resume_context=resume_context or None,
            reference_points=parse_ref_points(curr_q.reference_points_json)
        )

    raw_score = eval_res["score"]
    if not is_empty and is_overtime:
        # 超时轻扣分（不归零）：空作答已 0 分，无需再扣
        eval_res["score"] = apply_overtime_penalty(raw_score, overtime_sec)
        eval_res["evidence"] = list(eval_res.get("evidence") or []) + [
            f"本题超出建议限时 {overtime_sec} 秒，按超时规则轻扣分 "
            f"（{raw_score} → {eval_res['score']}），未作答完不直接归零"
        ]

    eval_obj = db.query(AnswerEvaluation).filter(AnswerEvaluation.answer_id == answer.id).first()
    if not eval_obj:
        eval_obj = AnswerEvaluation(
            answer_id=answer.id,
            interview_id=interview.id,
            total_score=eval_res["score"],
            dimensions_json=json.dumps(eval_res["dimensions"], ensure_ascii=False),
            evidence_json=json.dumps(eval_res["evidence"], ensure_ascii=False),
            weaknesses_json=json.dumps(eval_res["weaknesses"], ensure_ascii=False),
            missing_knowledge_json=json.dumps(eval_res["missing_knowledge"], ensure_ascii=False),
            suggestions_json=json.dumps(eval_res["suggestions"], ensure_ascii=False),
            next_action=eval_res.get("next_action", "CHANGE_TOPIC")
        )
        db.add(eval_obj)
    else:
        eval_obj.total_score = eval_res["score"]
        eval_obj.dimensions_json = json.dumps(eval_res["dimensions"], ensure_ascii=False)
        eval_obj.evidence_json = json.dumps(eval_res["evidence"], ensure_ascii=False)
        eval_obj.weaknesses_json = json.dumps(eval_res["weaknesses"], ensure_ascii=False)
        eval_obj.missing_knowledge_json = json.dumps(eval_res["missing_knowledge"], ensure_ascii=False)
        eval_obj.suggestions_json = json.dumps(eval_res["suggestions"], ensure_ascii=False)
        eval_obj.next_action = eval_res.get("next_action", "CHANGE_TOPIC")
    db.commit()

    # 自适应追问：按评分建议在卷面中插入同技能进阶/基础题
    followup = await _maybe_followup(db, interview, curr_q, eval_res)

    next_q = None
    if followup is not None:
        next_q = followup
    elif curr_q.seq < interview.total_questions:
        next_seq = curr_q.seq + 1
        next_q = db.query(InterviewQuestion).filter(
            InterviewQuestion.interview_id == interview.id,
            InterviewQuestion.seq == next_seq
        ).first()
        # 极端缺题（卷面被删改）时用 AI 兜底补一题
        if next_q is None:
            job_title = interview.job.title if interview.job else "综合岗位"
            q_data = await ai_provider.generate_question(
                job_title=job_title, seq=next_seq, difficulty=interview.difficulty,
                last_question=curr_q.text, last_answer=text, last_score=eval_res["score"],
                jd_text=jd_text or None, resume_context=resume_context or None
            )
            q_text = q_data.get("question") or ""
            if not q_text:
                raise HTTPException(status_code=500, detail="下一题缺失且 AI 兜底出题失败")
            next_q = InterviewQuestion(
                interview_id=interview.id,
                parent_question_id=curr_q.id,
                seq=next_seq,
                stage=q_data.get("stage") or "专业基础",
                question_type=q_data.get("question_type") or "PROFESSIONAL",
                skill_name=q_data.get("skill_name") or job_title,
                text=q_text,
                difficulty=q_data.get("difficulty") or interview.difficulty,
                hints=q_data.get("hints"),
                time_limit_sec=q_data.get("time_limit_sec") or 180,
                reference_points_json=json.dumps(
                    build_ai_reference_points(job_title, q_text), ensure_ascii=False
                ),
                source="AI_GENERATED"
            )
            db.add(next_q)
            db.commit()
            db.refresh(next_q)

    if next_q is not None:
        interview.current_question_seq = next_q.seq
        mark_question_shown(interview)  # 新题呈现，单题计时重新开始
        db.commit()

    finished = next_q is None
    report_id = None
    if finished:
        interview.current_question_shown_at = None
        interview.status = "COMPLETED"
        interview.ended_at = datetime.utcnow()
        db.commit()
        # 最后一题答完自动生成报告（前端直接跳报告页即可看到真实结算）
        rep = await finalize_interview(db, interview, user, force=False)
        report_id = rep.id

    return {
        "answer": answer,
        "eval_res": eval_res,
        "next_question": next_q,
        "is_followup": followup is not None and next_q is followup,
        "finished": finished,
        "report_id": report_id,
        "raw_score": raw_score,
        "overtime": is_overtime,
        "overtime_sec": overtime_sec,
        "is_empty": is_empty,
        "remaining_seconds": get_remaining_seconds(interview),
    }


async def finalize_interview(
    db: Session, interview: Interview, user: User,
    force: bool = False
) -> InterviewReport:
    """结算面试并生成报告（REST finish 与答题自动结算共用）。

    - 幂等：已 COMPLETED 且有报告 → 直接返回既有报告；
    - 未答完且非 force → 409（提示走中止）；
    - 完全无作答 → 409，不再生成写死的 82 分假报告；
    - 能力沉淀按最后作答技能（无则岗位名）记录，不再写死 "Redis"。
    """
    if interview.status == "COMPLETED" and interview.report:
        return interview.report

    answered = db.query(AnswerEvaluation).filter(
        AnswerEvaluation.interview_id == interview.id).count()
    if not force:
        if answered < (interview.total_questions or 0):
            raise HTTPException(
                status_code=409,
                detail=f"还有 {interview.total_questions - answered} 题未作答；如需提前结束请中止面试"
            )
    else:
        state_machine.ensure_not_terminal(interview.status, "提前交卷")
        state_machine.ensure(interview.status, state_machine.CAN_FINISH, "提前交卷")

    all_evals = db.query(AnswerEvaluation).filter(
        AnswerEvaluation.interview_id == interview.id).all()
    if not all_evals:
        raise HTTPException(status_code=409, detail="尚无任何作答记录，无法生成面试报告")

    scores = [e.total_score for e in all_evals]
    job_title = interview.job.title if interview.job else "综合岗位"
    jd_text, resume_context = load_interview_context(interview, db)
    qa_pairs = []
    for q in sorted(interview.questions, key=lambda x: x.seq):
        if q.answer and q.answer.evaluation:
            qa_pairs.append({
                "seq": q.seq,
                "question": q.text,
                "answer": q.answer.text,
                "score": q.answer.evaluation.total_score
            })
    report_data = await ai_provider.generate_report(
        interview.id, interview.total_questions, scores,
        qa_pairs=qa_pairs or None,
        job_title=job_title
    )

    rep = db.query(InterviewReport).filter(
        InterviewReport.interview_id == interview.id).first()
    if not rep:
        rep = InterviewReport(
            interview_id=interview.id,
            user_id=user.id,
            total_score=report_data["total_score"],
            performance_level=report_data["performance_level"],
            dimension_scores_json=json.dumps(report_data["dimension_scores"], ensure_ascii=False),
            strengths_json=json.dumps(report_data["strengths"], ensure_ascii=False),
            weaknesses_json=json.dumps(report_data["weaknesses"], ensure_ascii=False),
            suggestions_json=json.dumps(report_data["suggestions"], ensure_ascii=False),
            summary=report_data["summary"],
            status="COMPLETED"
        )
        db.add(rep)
    else:
        rep.total_score = report_data["total_score"]
        rep.performance_level = report_data["performance_level"]
        rep.dimension_scores_json = json.dumps(report_data["dimension_scores"], ensure_ascii=False)
        rep.strengths_json = json.dumps(report_data["strengths"], ensure_ascii=False)
        rep.weaknesses_json = json.dumps(report_data["weaknesses"], ensure_ascii=False)
        rep.suggestions_json = json.dumps(report_data["suggestions"], ensure_ascii=False)
        rep.summary = report_data["summary"]
        rep.status = "COMPLETED"

    # 能力沉淀：使用最后作答技能（真实），不再写死 Redis
    last_q = (db.query(InterviewQuestion)
              .filter(InterviewQuestion.interview_id == interview.id)
              .order_by(InterviewQuestion.seq.desc()).first())
    comp_name = (last_q.skill_name if last_q and last_q.skill_name else job_title) or job_title

    db.add(CompetencyHistory(
        user_id=user.id,
        competency_name=comp_name,
        score=report_data["total_score"],
        source_type="INTERVIEW",
        source_id=interview.id
    ))
    u_comp = db.query(UserCompetency).filter(
        UserCompetency.user_id == user.id,
        UserCompetency.competency_name == comp_name
    ).first()
    if u_comp:
        u_comp.score = report_data["total_score"]
    else:
        db.add(UserCompetency(user_id=user.id, competency_name=comp_name,
                              score=report_data["total_score"]))

    interview.status = "COMPLETED"
    interview.ended_at = interview.ended_at or datetime.utcnow()
    db.commit()

    # 学习路线联动（函数内 import 避免循环依赖）
    from app.api.v1.personal import generate_and_store_learning_plan, resolve_target_job
    target_job_title = resolve_target_job(user)
    await generate_and_store_learning_plan(
        db, user, target_job_title,
        jd_text=jd_text or None,
        gaps=report_data.get("weaknesses"),
        replace=True
    )
    db.commit()
    return rep
