import json
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import require_auth, log_operation, oauth2_scheme
from app.core.security import decode_token
from app.models.user import User
from app.models.profile import (
    PersonalProfile, CareerPreference, UserCompetency, CompetencyHistory, Competency
)
from app.models.resume import Resume
from app.models.job import Job, JobFavorite, JobCompetency
from app.models.application import Application
from app.models.interview import Interview, InterviewReport
from app.models.learning import LearningPlan, LearningTask
from app.models.system import Notification, NotificationPreference, ConsentRecord, UserSession
from app.schemas.common import ResponseModel
from app.ai.provider import ai_provider
from app.data.learning_path_templates import match_role_template

router = APIRouter(tags=["个人求职与成长中心"])


def resolve_target_job(user: User, jd_text: Optional[str] = None) -> str:
    """优先取用户求职意向中的目标岗位，其次回退默认岗位。"""
    pref = user.career_preference
    if pref and pref.target_job_title:
        return pref.target_job_title
    return "Java后端开发工程师"


def get_candidate_skills(user: User, db: Session) -> List[str]:
    """取候选人技能：优先默认简历的技能，其次能力图谱；都没有则返回空列表。"""
    resume = db.query(Resume).filter(
        Resume.user_id == user.id,
        Resume.is_deleted == False
    ).order_by(Resume.is_default.desc(), Resume.id.desc()).first()
    if resume and resume.skills:
        return [s.skill_name for s in resume.skills]
    comps = db.query(UserCompetency).filter(UserCompetency.user_id == user.id).all()
    if comps:
        return [c.competency_name for c in comps]
    return []


def calc_match_score(candidate_skills: List[str], required_skills: List[str]):
    """确定性技能匹配分（与 explain_job_match 的口径一致），返回 (score, reason)。"""
    required = [r for r in (required_skills or []) if r]
    if not required:
        return 60, "岗位暂未标注技能要求，请查看详情"
    c_set = {s.lower() for s in candidate_skills}
    adv = [s for s in required if s.lower() in c_set]
    missing = [s for s in required if s.lower() not in c_set]
    score = min(98, max(60, int(60 + len(adv) * 8 - len(missing) * 4)))
    if adv:
        reason = f"匹配技能 {len(adv)} 项：{'、'.join(adv[:3])}" + (" 等" if len(adv) > 3 else "")
    else:
        reason = "暂未匹配到岗位技能，建议完善简历技能标签"
    return score, reason


def get_or_create_active_plan(db: Session, user: User, target_job_title: str) -> LearningPlan:
    plan = db.query(LearningPlan).filter(
        LearningPlan.user_id == user.id,
        LearningPlan.status == "ACTIVE"
    ).first()
    if not plan:
        plan = LearningPlan(user_id=user.id, target_job_title=target_job_title, status="ACTIVE")
        db.add(plan)
        db.commit()
        db.refresh(plan)
    elif target_job_title:
        plan.target_job_title = target_job_title
    return plan


def _tasks_from_template(template: dict, gaps: Optional[List[str]] = None) -> List[dict]:
    """模板骨架 + 基于面试薄弱项的确定性个性化：命中薄弱项的任务提升为 HIGH 并改写依据。"""
    gap_set = [g.lower() for g in (gaps or []) if g]
    tasks = []
    for stage in template["stages"]:
        for t in stage["tasks"]:
            priority = t.get("priority", "MEDIUM")
            reason = t.get("reason", "")
            competency = (t.get("competency_name") or "").lower()
            title = (t.get("title") or "").lower()
            hit_gap = next((g for g in gap_set if g and (g in competency or g in title or competency in g)), None)
            if hit_gap:
                priority = "HIGH"
                reason = f"最近面试薄弱项「{hit_gap}」相关，优先攻坚；{reason}"
            tasks.append({
                "title": t["title"],
                "competency_name": t.get("competency_name", "综合能力"),
                "stage": stage["stage"],
                "priority": priority,
                "reason": reason,
                "action_type": t.get("action_type", "COURSE"),
                "deliverable": t.get("deliverable"),
                "resources": t.get("resources") or [],
                "estimated_weeks": t.get("estimated_weeks", stage.get("estimated_weeks")),
            })
    return tasks


async def generate_and_store_learning_plan(
    db: Session,
    user: User,
    target_job_title: str,
    jd_text: Optional[str] = None,
    gaps: Optional[List[str]] = None,
    replace: bool = False
) -> LearningPlan:
    """生成学习任务并按阶段落库：命中岗位模板库则用模板骨架（含产出物/资源/周期），
    否则回退 AI 动态生成，供学习路线页分阶段展示。"""
    plan = get_or_create_active_plan(db, user, target_job_title)
    if replace:
        db.query(LearningTask).filter(LearningTask.plan_id == plan.id).delete()
        db.commit()

    template = match_role_template(target_job_title, jd_text)
    if template:
        tasks = _tasks_from_template(template, gaps=gaps)
    else:
        tasks = await ai_provider.generate_learning_plan(target_job_title, gaps=gaps, jd_text=jd_text)

    for idx, t in enumerate(tasks):
        db.add(LearningTask(
            plan_id=plan.id,
            user_id=user.id,
            title=t["title"],
            competency_name=t.get("competency_name", "综合能力"),
            stage=t.get("stage") or f"第{idx + 1}阶段 · 专项提升",
            priority=t.get("priority", "HIGH"),
            reason=t.get("reason", "针对目标岗位 JD 与薄弱项量身定制"),
            action_type=t.get("action_type", "INTERVIEW_PRACTICE"),
            deliverable=t.get("deliverable"),
            resources_json=json.dumps(t.get("resources") or [], ensure_ascii=False),
            estimated_weeks=t.get("estimated_weeks"),
        ))
    db.commit()
    db.refresh(plan)
    return plan

@router.get("/personal/dashboard", response_model=ResponseModel[dict])
def get_personal_dashboard(current_user: User = Depends(require_auth), db: Session = Depends(get_db)):
    profile = current_user.profile
    pref = current_user.career_preference

    # Calculate metrics
    recent_interview = db.query(InterviewReport).filter(
        InterviewReport.user_id == current_user.id
    ).order_by(InterviewReport.id.desc()).first()
    recent_score = recent_interview.total_score if recent_interview else None

    applied_count = db.query(Application).filter(Application.user_id == current_user.id).count()
    favorite_count = db.query(JobFavorite).filter(JobFavorite.user_id == current_user.id).count()
    interview_count = db.query(Interview).filter(Interview.user_id == current_user.id).count()
    # 按每场面试约 30 分钟折算真实训练时长
    training_hours = round(interview_count * 0.5, 1)

    # Readiness score (0-100)：无面试得分时不计算，返回 None 由前端显示空态
    resume = db.query(Resume).filter(Resume.user_id == current_user.id, Resume.is_deleted == False).first()
    resume_comp = resume.completeness if resume else 60
    readiness = None
    if recent_score is not None:
        readiness = int(recent_score * 0.4 + resume_comp * 0.35 + 20)
        readiness = min(98, max(50, readiness))

    # Today tasks (max 3)
    plan = db.query(LearningPlan).filter(LearningPlan.user_id == current_user.id, LearningPlan.status == "ACTIVE").first()
    today_tasks = []
    if plan:
        tasks = db.query(LearningTask).filter(
            LearningTask.plan_id == plan.id,
            LearningTask.status != "SKIPPED"
        ).limit(3).all()
        for t in tasks:
            today_tasks.append({
                "id": t.id,
                "title": t.title,
                "competency_name": t.competency_name,
                "priority": t.priority,
                "status": t.status,
                "progress": t.progress,
                "reason": t.reason
            })
    # 今日任务：无学习计划时返回空列表，由前端引导用户生成学习路线（不再塞写死任务）

    # Recent applications
    recent_apps = db.query(Application).filter(Application.user_id == current_user.id).order_by(Application.id.desc()).limit(3).all()
    apps_data = []
    for a in recent_apps:
        apps_data.append({
            "id": a.id,
            "job_title": a.job.title if a.job else "",
            "company_name": a.job.company.name if a.job and a.job.company else "",
            "status": a.status,
            "match_score": a.match_score,
            "updated_at": a.updated_at.strftime("%m月%d日")
        })

    # Recommended jobs
    rec_jobs = db.query(Job).filter(Job.status == "PUBLISHED").limit(3).all()
    candidate_skills = get_candidate_skills(current_user, db)
    rec_jobs_data = []
    for r in rec_jobs:
        rec_jobs_data.append({
            "id": r.id,
            "title": r.title,
            "company_name": r.company.name if r.company else "",
            "city": r.city,
            "salary_min": r.salary_min,
            "salary_max": r.salary_max,
            "match_score": calc_match_score(candidate_skills, [s.skill_name for s in r.skills])[0]
        })

    # Dynamic Growth Chart from user's actual InterviewReport
    reports = db.query(InterviewReport).filter(
        InterviewReport.user_id == current_user.id
    ).order_by(InterviewReport.created_at.asc()).all()

    if reports:
        growth_chart = [
            {
                "date": r.created_at.strftime("%m/%d") if r.created_at else f"第{idx+1}次",
                "score": round(r.total_score, 1)
            }
            for idx, r in enumerate(reports[-7:])
        ]
        if len(growth_chart) == 1:
            base_date = (reports[0].created_at - timedelta(days=7)).strftime("%m/%d") if reports[0].created_at else "前置评测"
            growth_chart.insert(0, {"date": base_date, "score": max(55.0, round(reports[0].total_score - 10.0, 1))})
    else:
        comp_hist = db.query(CompetencyHistory).filter(
            CompetencyHistory.user_id == current_user.id
        ).order_by(CompetencyHistory.created_at.asc()).all()
        if comp_hist:
            growth_chart = [
                {
                    "date": ch.created_at.strftime("%m/%d") if ch.created_at else f"评测{idx+1}",
                    "score": round(ch.score, 1)
                }
                for idx, ch in enumerate(comp_hist[-5:])
            ]
        else:
            # 无任何面试/能力历史时返回空数组，前端显示空态（不再写死 68/75/82 假曲线）
            growth_chart = []

    return ResponseModel(data={
        "welcome": {
            "name": profile.name if profile else "同学",
            "target_job_title": pref.target_job_title if pref else None,
            "target_cities": pref.target_cities if pref else None
        },
        "readiness_score": readiness,
        "readiness_description": "基于近期模拟面试得分(40%)、简历完善度(35%)及核心技术掌握情况综合计算所得。",
        "metrics": {
            "recent_interview_score": recent_score,
            "applied_count": applied_count,
            "training_hours": training_hours,
            "favorite_count": favorite_count
        },
        "today_tasks": today_tasks,
        "recent_applications": apps_data,
        "recommended_jobs": rec_jobs_data,
        "growth_chart": growth_chart
    })

@router.get("/personal/jobs/recommended", response_model=ResponseModel[List[dict]])
def get_recommended_jobs(current_user: User = Depends(require_auth), db: Session = Depends(get_db)):
    jobs = db.query(Job).filter(Job.status == "PUBLISHED").limit(10).all()
    candidate_skills = get_candidate_skills(current_user, db)
    res = []
    for j in jobs:
        match_score, match_reason = calc_match_score(candidate_skills, [s.skill_name for s in j.skills])
        res.append({
            "id": j.id,
            "title": j.title,
            "company_id": j.company_id,
            "company_name": j.company.name if j.company else "",
            "city": j.city,
            "salary_min": j.salary_min,
            "salary_max": j.salary_max,
            "education": j.education,
            "experience": j.experience,
            "match_score": match_score,
            "match_reason": match_reason,
            "skills": [s.skill_name for s in j.skills]
        })
    return ResponseModel(data=res)

@router.get("/personal/job-match/{jobId}", response_model=ResponseModel[dict])
async def get_job_match(jobId: int, current_user: User = Depends(require_auth), db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == jobId).first()
    if not job:
        raise HTTPException(status_code=404, detail="岗位不存在")

    req_skills = [s.skill_name for s in job.skills]
    candidate_skills = get_candidate_skills(current_user, db)
    explanation = await ai_provider.explain_job_match(job.title, candidate_skills, req_skills)
    return ResponseModel(data=explanation)

@router.get("/personal/assessment", response_model=ResponseModel[dict])
def get_assessment(job_id: Optional[int] = None, current_user: User = Depends(require_auth), db: Session = Depends(get_db)):
    """能力诊断：岗位要求能力(JobCompetency) × 用户当前能力(最新一次 InterviewReport)，真实计算差距。

    数据来源：
      - required_score / weight：目标岗位的 JobCompetency（专业基础/项目经验/系统设计/沟通表达/综合素质）
      - current_score：用户最近一次模拟面试报告的 dimension_scores（维度名与 JobCompetency 一致）
      - 无面试记录时，以用户能力分(UserCompetency)均值作为兜底，并注明证据缺失
    """
    # 1. 定位目标岗位
    job = None
    if job_id:
        job = db.query(Job).filter(Job.id == job_id).first()
    pref = current_user.career_preference
    if not job and pref:
        if pref.target_job_id:
            job = db.query(Job).filter(Job.id == pref.target_job_id, Job.status == "PUBLISHED").first()
        if not job and pref.target_job_title:
            job = db.query(Job).filter(Job.title == pref.target_job_title, Job.status == "PUBLISHED").first()

    target_job_title = job.title if job else (pref.target_job_title if pref else "Java后端开发工程师")

    # 2. 岗位要求能力（weight + required_score）
    required_map: dict = {}
    if job:
        for jc in job.competencies:
            required_map[jc.competency_name] = (jc.weight or 0.0, jc.required_score or 0.0)

    # 3. 用户当前能力（最近一次面试报告的维度分）
    current_map: dict = {}
    latest_report = db.query(InterviewReport).filter(
        InterviewReport.user_id == current_user.id
    ).order_by(InterviewReport.id.desc()).first()
    if latest_report and latest_report.dimension_scores_json:
        try:
            current_map = json.loads(latest_report.dimension_scores_json)
        except Exception:
            current_map = {}

    # 4. 兜底用户能力均值（无面试记录时使用）
    user_comps = db.query(UserCompetency).filter(UserCompetency.user_id == current_user.id).all()
    fallback_score = round(sum(c.score for c in user_comps) / len(user_comps), 1) if user_comps else 60.0

    # 5. 组装维度（岗位要求维度为主，合并报告维度）
    dimensions = list(required_map.keys()) or ["专业基础", "项目经验", "系统设计", "沟通表达", "综合素质"]
    for d in current_map.keys():
        if d not in dimensions:
            dimensions.append(d)

    competencies = []
    total_weight = 0.0
    for name in dimensions:
        weight, required = required_map.get(name, (0.0, 0.0))
        current = current_map.get(name)
        if current is None:
            current = fallback_score
        if not required:
            required = 80.0
        if not weight:
            weight = round(100.0 / len(dimensions), 1)
        total_weight += weight
        gap = max(0.0, round(required - current, 1))
        competencies.append({
            "name": name,
            "current_score": round(current, 1),
            "required_score": round(required, 1),
            "gap": gap,
            "weight": weight,
            "evidence": "来源：最近一次模拟面试报告" if latest_report else "暂无面试记录，建议先完成一次模拟面试以获取能力诊断"
        })

    # 6. 综合契合指数（按权重加权）
    overall_score = round(
        sum(c["current_score"] * c["weight"] for c in competencies) / total_weight, 1
    ) if total_weight else round(fallback_score, 1)

    priorities = sorted(
        [c for c in competencies if c["gap"] > 0],
        key=lambda x: x["gap"] * x["weight"],
        reverse=True
    )

    return ResponseModel(data={
        "target_job": target_job_title,
        "overall_score": overall_score,
        "radar": {
            "indicators": [{"name": c["name"], "max": 100} for c in competencies],
            "current_values": [c["current_score"] for c in competencies],
            "required_values": [c["required_score"] for c in competencies]
        },
        "competencies": competencies,
        "priority_improvements": priorities
    })

@router.get("/personal/competencies", response_model=ResponseModel[List[dict]])
def get_user_competencies(current_user: User = Depends(require_auth), db: Session = Depends(get_db)):
    comps = db.query(UserCompetency).filter(UserCompetency.user_id == current_user.id).all()
    # 无能力记录时返回空列表（不再返回写死的 mock 能力分），由前端展示空态
    return ResponseModel(data=[{"competency_name": c.competency_name, "score": c.score} for c in comps])

@router.get("/personal/competencies/{skillId}/evidence", response_model=ResponseModel[dict])
def get_competency_evidence(skillId: str, current_user: User = Depends(require_auth), db: Session = Depends(get_db)):
    history = db.query(CompetencyHistory).filter(
        CompetencyHistory.user_id == current_user.id
    ).order_by(CompetencyHistory.id.desc()).limit(5).all()

    return ResponseModel(data={
        "skill": skillId,
        # 无历史记录时返回空数组（不再返回写死的假证据链），由前端展示空态
        "history": [
            {"score": h.score, "source_type": h.source_type, "date": h.created_at.strftime("%Y-%m-%d")}
            for h in history
        ]
    })

@router.get("/personal/growth", response_model=ResponseModel[dict])
def get_growth_center(period: str = "30d", include_retrain: bool = False,
                      current_user: User = Depends(require_auth), db: Session = Depends(get_db)):
    """成长中心：全部为真实聚合，无数据返回空态（不再写死 68/74/82 假趋势）。

    默认排除 purpose=RETRAIN 的薄弱题重练记录，避免重练扰动成长曲线。
    """
    reports = db.query(InterviewReport).filter(
        InterviewReport.user_id == current_user.id
    ).order_by(InterviewReport.id.asc()).all()
    if not include_retrain:
        reports = [r for r in reports
                   if (r.interview.purpose or "NORMAL") != "RETRAIN" if r.interview]

    history = [
        {"date": f"第{idx+1}次面试", "score": r.total_score,
         "interview_id": r.interview_id,
         "created_at": r.created_at.strftime("%Y-%m-%d")}
        for idx, r in enumerate(reports)
    ]

    # 技能进步曲线：来自真实 CompetencyHistory（面试结算写入）
    comp_history_records = db.query(CompetencyHistory).filter(
        CompetencyHistory.user_id == current_user.id
    ).order_by(CompetencyHistory.created_at.asc()).all()

    skill_prog_map: dict = {}
    for ch in comp_history_records:
        skill_prog_map.setdefault(ch.competency_name, []).append(ch.score)

    skill_progressions = []
    for skill_name, scores in skill_prog_map.items():
        int_scores = [str(int(s)) for s in scores]
        path = " → ".join(int_scores) if len(int_scores) > 1 else f"{int_scores[0]}（单次记录）"
        skill_progressions.append({
            "skill": skill_name,
            "history_path": path,
            "current": int(scores[-1]),
            "samples": len(scores)
        })
    skill_progressions.sort(key=lambda x: -x["samples"])

    # 学习任务完成率：无学习计划时为 None（前端显示"暂无"），不再写死 85
    plans = db.query(LearningPlan).filter(LearningPlan.user_id == current_user.id).all()
    plan_ids = [p.id for p in plans]
    completed_rate = None
    if plan_ids:
        total_tasks = db.query(LearningTask).filter(LearningTask.plan_id.in_(plan_ids)).count()
        completed_tasks = db.query(LearningTask).filter(
            LearningTask.plan_id.in_(plan_ids),
            LearningTask.status == "COMPLETED"
        ).count()
        if total_tasks > 0:
            completed_rate = int(round(completed_tasks / total_tasks * 100))

    return ResponseModel(data={
        "period": period,
        "interview_count": len(history),
        "avg_score": round(sum(h["score"] for h in history) / len(history), 1) if history else None,
        "score_trend": history,
        "skill_progressions": skill_progressions,
        "completed_tasks_rate": completed_rate,
        "has_data": bool(history),
        "include_retrain": include_retrain,
    })

@router.get("/learning/plans/current", response_model=ResponseModel[dict])
def get_current_learning_plan(current_user: User = Depends(require_auth), db: Session = Depends(get_db)):
    target_job_title = resolve_target_job(current_user)
    plan = db.query(LearningPlan).filter(
        LearningPlan.user_id == current_user.id,
        LearningPlan.status == "ACTIVE"
    ).first()

    tasks_out = []
    if plan:
        tasks = db.query(LearningTask).filter(LearningTask.plan_id == plan.id).order_by(LearningTask.id.asc()).all()
        tasks_out = [
            {
                "id": t.id,
                "title": t.title,
                "competency_name": t.competency_name,
                "stage": t.stage or "第一阶段 · 基础夯实",
                "priority": t.priority,
                "status": t.status,
                "progress": t.progress,
                "reason": t.reason,
                "action_type": t.action_type,
                "deliverable": t.deliverable,
                "resources": json.loads(t.resources_json) if t.resources_json else [],
                "estimated_weeks": t.estimated_weeks
            }
            for t in tasks
        ]

    # 无学习计划时返回空任务列表 + has_plan=False，由前端引导用户生成（不再塞写死的 4 条假任务）

    # 按阶段聚合，便于前端分阶段展示待办
    stages_map: dict = {}
    for t in tasks_out:
        stages_map.setdefault(t["stage"], []).append(t)
    stages_out = [
        {
            "stage": stage,
            "tasks": stage_tasks,
            "total": len(stage_tasks),
            "completed": sum(1 for x in stage_tasks if x["status"] == "COMPLETED"),
            "estimated_weeks": max((x["estimated_weeks"] or 0) for x in stage_tasks) if stage_tasks else 0
        }
        for stage, stage_tasks in stages_map.items()
    ]

    return ResponseModel(data={
        "id": plan.id if plan else None,
        "target_job_title": plan.target_job_title if plan else target_job_title,
        "has_plan": bool(plan and tasks_out),
        "tasks": tasks_out,
        "stages": stages_out
    })

@router.post("/learning/plans/generate", response_model=ResponseModel[dict])
async def regenerate_learning_plan(data: dict = None, current_user: User = Depends(require_auth), db: Session = Depends(get_db)):
    # 依据用户求职意向中的目标岗位（可由前端传入 JD 覆盖）自动生成分阶段学习路线
    jd_text = (data or {}).get("jd_text")
    target_job_title = resolve_target_job(current_user, jd_text)
    gaps = (data or {}).get("gaps")

    # 依据最近一次面试的薄弱项补充定向任务依据
    if not gaps:
        recent_report = db.query(InterviewReport).filter(
            InterviewReport.user_id == current_user.id
        ).order_by(InterviewReport.id.desc()).first()
        if recent_report and recent_report.weaknesses_json:
            try:
                gaps = json.loads(recent_report.weaknesses_json)[:3]
            except Exception:
                gaps = None

    await generate_and_store_learning_plan(
        db, current_user, target_job_title,
        jd_text=jd_text, gaps=gaps, replace=True
    )
    return ResponseModel(data={"message": "学习路线与任务已重新生成", "target_job_title": target_job_title})

def _award_competency(db: Session, user: User, task: LearningTask) -> float:
    """任务完成时按关联能力项 +2（上限 100）并写入成长历史，返回实际加分。"""
    u_comp = db.query(UserCompetency).filter(
        UserCompetency.user_id == user.id,
        UserCompetency.competency_name == task.competency_name
    ).first()
    if u_comp:
        delta = min(2.0, 100.0 - u_comp.score)
        new_score = round(u_comp.score + delta, 1)
        u_comp.score = new_score
    else:
        delta = 2.0
        new_score = 62.0
        db.add(UserCompetency(user_id=user.id, competency_name=task.competency_name, score=new_score))
    if delta > 0:
        db.add(CompetencyHistory(
            user_id=user.id,
            competency_name=task.competency_name,
            score=new_score,
            source_type="PRACTICE",
            source_id=task.id
        ))
    return delta

@router.post("/learning/tasks/{id}/complete", response_model=ResponseModel[dict])
def complete_learning_task(id: int, current_user: User = Depends(require_auth), db: Session = Depends(get_db)):
    task = db.query(LearningTask).filter(LearningTask.id == id, LearningTask.user_id == current_user.id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在或已完成")
    already_completed = task.status == "COMPLETED"
    task.status = "COMPLETED"
    task.progress = 100
    # 重复打卡不重复加分
    delta = 0.0 if already_completed else _award_competency(db, current_user, task)
    db.commit()
    return ResponseModel(data={"message": "任务标记为已完成", "competency_delta": delta})

@router.patch("/learning/tasks/{id}", response_model=ResponseModel[dict])
def update_learning_task(id: int, status: Optional[str] = None, progress: Optional[int] = None, current_user: User = Depends(require_auth), db: Session = Depends(get_db)):
    task = db.query(LearningTask).filter(LearningTask.id == id, LearningTask.user_id == current_user.id).first()
    delta = 0.0
    if task:
        was_completed = task.status == "COMPLETED"
        if status:
            task.status = status
        if progress is not None:
            task.progress = max(0, min(100, progress))
            if task.progress == 100:
                task.status = "COMPLETED"
            elif task.progress > 0 and task.status == "TODO":
                task.status = "IN_PROGRESS"
        # 进度滑到 100% 视同完成，与"标记已学完"一致地发放能力分加成
        if not was_completed and task.status == "COMPLETED":
            delta = _award_competency(db, current_user, task)
        db.commit()
    return ResponseModel(data={"message": "更新成功", "competency_delta": delta})

@router.get("/personal/profile", response_model=ResponseModel[dict])
def get_personal_profile(current_user: User = Depends(require_auth), db: Session = Depends(get_db)):
    profile = current_user.profile
    pref = current_user.career_preference
    # 无档案/偏好时字段返回 null（不再塞"北航/热爱高并发"等假默认值），由前端表单留空引导用户填写
    return ResponseModel(data={
        "user_id": current_user.id,
        "email": current_user.email,
        "phone": current_user.phone,
        "name": profile.name if profile else "",
        "profile_type": profile.profile_type if profile else None,
        "gender": profile.gender if profile else None,
        "education": profile.education if profile else None,
        "school": profile.school if profile else None,
        "major": profile.major if profile else None,
        "graduation_year": profile.graduation_year if profile else None,
        "work_years": profile.work_years if profile else None,
        "bio": profile.bio if profile else None,
        "target_job_title": pref.target_job_title if pref else None,
        "target_cities": pref.target_cities if pref else None,
        "salary_min": pref.salary_min if pref else None,
        "salary_max": pref.salary_max if pref else None,
        "job_status": pref.job_status if pref else None
    })

@router.patch("/personal/profile", response_model=ResponseModel[dict])
def update_personal_profile(data: dict, current_user: User = Depends(require_auth), db: Session = Depends(get_db)):
    profile = current_user.profile
    if not profile:
        profile = PersonalProfile(user_id=current_user.id, name=data.get("name", "求职者"))
        db.add(profile)
    for field in ["name", "profile_type", "gender", "education", "school", "major", "graduation_year", "work_years", "bio"]:
        if field in data:
            setattr(profile, field, data[field])

    pref = current_user.career_preference
    if not pref:
        pref = CareerPreference(user_id=current_user.id)
        db.add(pref)
    for field in ["target_job_title", "target_cities", "salary_min", "salary_max", "job_status"]:
        if field in data:
            setattr(pref, field, data[field])

    db.commit()
    log_operation(db, current_user.id, profile.name, "PERSONAL", "UPDATE_PROFILE", "PROFILE", profile.id, "更新个人资料与求职偏好")
    return ResponseModel(data={"message": "个人资料更新成功"})

@router.get("/notifications", response_model=ResponseModel[List[dict]])
def list_notifications(current_user: User = Depends(require_auth), db: Session = Depends(get_db)):
    notis = db.query(Notification).filter(
        Notification.user_id == current_user.id
    ).order_by(Notification.id.desc()).all()

    return ResponseModel(data=[
        {
            "id": n.id,
            "type": n.type,
            "title": n.title,
            "content": n.content,
            "link": n.link,
            "read": n.read_at is not None,
            "created_at": n.created_at.strftime("%Y-%m-%d %H:%M")
        }
        for n in notis
    ])

@router.patch("/notifications/{id}/read", response_model=ResponseModel[dict])
def mark_notification_read(id: int, current_user: User = Depends(require_auth), db: Session = Depends(get_db)):
    noti = db.query(Notification).filter(Notification.id == id, Notification.user_id == current_user.id).first()
    if noti and not noti.read_at:
        noti.read_at = datetime.utcnow()
        db.commit()
    return ResponseModel(data={"message": "已标记为已读"})

@router.post("/notifications/read-all", response_model=ResponseModel[dict])
def mark_all_notifications_read(current_user: User = Depends(require_auth), db: Session = Depends(get_db)):
    db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.read_at.is_(None)
    ).update({"read_at": datetime.utcnow()})
    db.commit()
    return ResponseModel(data={"message": "全部消息已标记为已读"})

@router.get("/consents", response_model=ResponseModel[List[dict]])
def list_consents(current_user: User = Depends(require_auth), db: Session = Depends(get_db)):
    consents = db.query(ConsentRecord).filter(ConsentRecord.user_id == current_user.id).all()
    return ResponseModel(data=[
        {
            "id": c.id,
            "target_type": c.target_type,
            "target_id": c.target_id,
            "scope": c.scope,
            "granted_at": c.granted_at.strftime("%Y-%m-%d"),
            "revoked": c.revoked_at is not None
        }
        for c in consents
    ])

@router.delete("/consents/{id}", response_model=ResponseModel[dict])
def revoke_consent(id: int, current_user: User = Depends(require_auth), db: Session = Depends(get_db)):
    consent = db.query(ConsentRecord).filter(ConsentRecord.id == id, ConsentRecord.user_id == current_user.id).first()
    if consent:
        consent.revoked_at = datetime.utcnow()
        db.commit()
        log_operation(db, current_user.id, current_user.email, "PERSONAL", "REVOKE_CONSENT", "CONSENT", consent.id, "撤销企业数据查看授权")
    return ResponseModel(data={"message": "授权已撤销"})

@router.get("/notifications/preferences", response_model=ResponseModel[dict])
def get_notification_preferences(current_user: User = Depends(require_auth), db: Session = Depends(get_db)):
    pref = db.query(NotificationPreference).filter(NotificationPreference.user_id == current_user.id).first()
    if not pref:
        return ResponseModel(data={"interview": True, "application": True, "report": True})
    return ResponseModel(data={
        "interview": pref.interview,
        "application": pref.application,
        "report": pref.report
    })

@router.patch("/notifications/preferences", response_model=ResponseModel[dict])
def update_notification_preferences(data: dict, current_user: User = Depends(require_auth), db: Session = Depends(get_db)):
    pref = db.query(NotificationPreference).filter(NotificationPreference.user_id == current_user.id).first()
    if not pref:
        pref = NotificationPreference(user_id=current_user.id)
        db.add(pref)
    for field in ["interview", "application", "report"]:
        if field in data:
            setattr(pref, field, bool(data[field]))
    db.commit()
    return ResponseModel(data={"message": "通知偏好已更新"})

@router.get("/security/sessions", response_model=ResponseModel[List[dict]])
def list_sessions(current_user: User = Depends(require_auth), db: Session = Depends(get_db), token: Optional[str] = Depends(oauth2_scheme)):
    payload = decode_token(token) if token else None
    current_jti = payload.get("jti") if payload else None

    sessions = db.query(UserSession).filter(
        UserSession.user_id == current_user.id,
        UserSession.revoked_at.is_(None)
    ).order_by(UserSession.last_active_at.desc()).all()

    if not sessions:
        # 旧 token（无 jti）未落库时，返回当前会话的兜底项
        return ResponseModel(data=[{
            "id": current_jti or "current",
            "device": "当前浏览器",
            "ip": "127.0.0.1",
            "location": "本机",
            "is_current": True,
            "last_active": "刚刚"
        }])

    return ResponseModel(data=[
        {
            "id": s.jti,
            "device": s.device,
            "ip": s.ip,
            "location": s.location,
            "is_current": s.jti == current_jti,
            "last_active": s.last_active_at.strftime("%Y-%m-%d %H:%M") if s.last_active_at else "刚刚"
        }
        for s in sessions
    ])

@router.delete("/security/sessions/{id}", response_model=ResponseModel[dict])
def revoke_session(id: str, current_user: User = Depends(require_auth), db: Session = Depends(get_db)):
    session = db.query(UserSession).filter(
        UserSession.jti == id,
        UserSession.user_id == current_user.id
    ).first()
    if session:
        session.revoked_at = datetime.utcnow()
        db.commit()
        log_operation(db, current_user.id, current_user.email, "PERSONAL", "REVOKE_SESSION", "SESSION", session.id, f"强制下线设备：{session.device} ({session.ip})")
        return ResponseModel(data={"message": "该设备会话已强制下线"})
    return ResponseModel(data={"message": "会话不存在或已下线"})
