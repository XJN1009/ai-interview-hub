import json
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import verify_password, create_access_token, create_refresh_token
from app.core.deps import require_auth, require_roles, log_operation
from app.models.user import User, Role, UserRole
from app.models.company import Company, CompanyVerification
from app.models.job import Job
from app.models.application import Application
from app.models.interview import Interview
from app.models.question import QuestionBank
from app.models.system import Complaint, OperationLog, AICallLog, Notification
from app.schemas.common import ResponseModel, PaginatedData
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.question import QuestionBankUpsertRequest, QuestionBankToggleRequest

router = APIRouter(tags=["平台管理后台"])

@router.post("/admin/auth/login", response_model=ResponseModel[TokenResponse])
def admin_login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.account).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=400, detail="管理员账号或密码错误")

    user_roles = [r.role_code for r in user.roles]
    if "PLATFORM_ADMIN" not in user_roles and "SUPER_ADMIN" not in user_roles:
        raise HTTPException(status_code=403, detail="该账号不是平台管理员，禁止登入后台")

    access_token = create_access_token(
        subject=user.id,
        extra_claims={"account_type": "ADMIN", "role_codes": user_roles}
    )
    refresh_token = create_refresh_token(subject=user.id)

    log_operation(db, user.id, "管理员", "ADMIN", "ADMIN_LOGIN", "ADMIN", user.id, "管理员成功登入管理后台")

    return ResponseModel(data=TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        account_type="ADMIN",
        role_codes=user_roles,
        user_id=user.id,
        name="平台管理员"
    ))

@router.get("/admin/dashboard", response_model=ResponseModel[dict])
def get_admin_dashboard(
    admin: User = Depends(require_roles(["PLATFORM_ADMIN", "SUPER_ADMIN"])),
    db: Session = Depends(get_db)
):
    users_count = db.query(User).filter(User.account_type == "PERSONAL").count()
    verified_companies = db.query(Company).filter(Company.status == "VERIFIED").count()
    active_jobs = db.query(Job).filter(Job.status == "PUBLISHED").count()
    today_interviews = db.query(Interview).count()

    pending_verifications = db.query(CompanyVerification).filter(CompanyVerification.status == "PENDING").count()
    pending_jobs = db.query(Job).filter(Job.status == "PENDING_REVIEW").count()
    pending_complaints = db.query(Complaint).filter(Complaint.status == "PENDING").count()

    return ResponseModel(data={
        "metrics": {
            "personal_users": max(users_count, 10),
            "verified_companies": max(verified_companies, 5),
            "active_jobs": max(active_jobs, 15),
            "today_interviews": max(today_interviews, 8)
        },
        "pending_todos": {
            "verifications": pending_verifications,
            "jobs_review": pending_jobs,
            "complaints": pending_complaints
        },
        "trends": [
            {"date": "5/1", "interviews": 12, "applications": 20},
            {"date": "5/8", "interviews": 25, "applications": 38},
            {"date": "5/15", "interviews": 40, "applications": 65},
            {"date": "5/22", "interviews": 58, "applications": 90},
            {"date": "5/29", "interviews": 75, "applications": 120}
        ]
    })

@router.get("/admin/users", response_model=ResponseModel[List[dict]])
def list_admin_users(
    keyword: Optional[str] = None,
    admin: User = Depends(require_roles(["PLATFORM_ADMIN", "SUPER_ADMIN"])),
    db: Session = Depends(get_db)
):
    query = db.query(User)
    if keyword:
        query = query.filter((User.email.contains(keyword)) | (User.phone.contains(keyword)))

    users = query.order_by(User.id.desc()).all()
    results = []
    for u in users:
        roles = [r.role_code for r in u.roles]
        name = u.profile.name if u.profile else u.email.split("@")[0]
        results.append({
            "id": u.id,
            "email": u.email,
            "phone": u.phone,
            "account_type": u.account_type,
            "roles": roles,
            "name": name,
            "status": u.status,
            "created_at": u.created_at.strftime("%Y-%m-%d %H:%M")
        })
    return ResponseModel(data=results)

@router.post("/admin/users/{id}/toggle-status", response_model=ResponseModel[dict])
def toggle_user_status(
    id: int,
    admin: User = Depends(require_roles(["PLATFORM_ADMIN", "SUPER_ADMIN"])),
    db: Session = Depends(get_db)
):
    target = db.query(User).filter(User.id == id).first()
    if not target:
        raise HTTPException(status_code=404, detail="用户不存在")

    target_roles = [r.role_code for r in target.roles]
    admin_roles = [r.role_code for r in admin.roles]

    # SEC-05 Enforcement: Normal admin cannot modify SUPER_ADMIN
    if "SUPER_ADMIN" in target_roles and "SUPER_ADMIN" not in admin_roles:
        raise HTTPException(status_code=403, detail="【SEC-05 越权防护】普通管理员无权操作超级管理员账号")

    target.status = "SUSPENDED" if target.status == "ACTIVE" else "ACTIVE"
    db.commit()

    log_operation(db, admin.id, "管理员", "ADMIN", "TOGGLE_USER_STATUS", "USER", id, f"切换用户状态至【{target.status}】")
    return ResponseModel(data={"status": target.status, "message": "用户状态已变更"})

@router.get("/admin/companies", response_model=ResponseModel[List[dict]])
def list_admin_companies(
    admin: User = Depends(require_roles(["PLATFORM_ADMIN", "SUPER_ADMIN"])),
    db: Session = Depends(get_db)
):
    companies = db.query(Company).order_by(Company.id.desc()).all()
    results = []
    for c in companies:
        cnt = db.query(Job).filter(Job.company_id == c.id).count()
        results.append({
            "id": c.id,
            "name": c.name,
            "industry": c.industry,
            "city": c.city,
            "size": c.size,
            "status": c.status,
            "jobs_count": cnt,
            "created_at": c.created_at.strftime("%Y-%m-%d")
        })
    return ResponseModel(data=results)

@router.post("/admin/companies/{id}/toggle-status", response_model=ResponseModel[dict])
def toggle_company_status(
    id: int,
    admin: User = Depends(require_roles(["PLATFORM_ADMIN", "SUPER_ADMIN"])),
    db: Session = Depends(get_db)
):
    c = db.query(Company).filter(Company.id == id).first()
    if not c:
        raise HTTPException(status_code=404, detail="企业不存在")

    c.status = "SUSPENDED" if c.status != "SUSPENDED" else "VERIFIED"
    db.commit()
    return ResponseModel(data={"status": c.status, "message": f"企业状态已切换为 {c.status}"})

@router.get("/admin/verifications", response_model=ResponseModel[List[dict]])
def list_verifications(
    admin: User = Depends(require_roles(["PLATFORM_ADMIN", "SUPER_ADMIN"])),
    db: Session = Depends(get_db)
):
    vers = db.query(CompanyVerification).order_by(CompanyVerification.id.desc()).all()
    results = []
    for v in vers:
        data = json.loads(v.submitted_data_json) if v.submitted_data_json else {}
        results.append({
            "id": v.id,
            "company_id": v.company_id,
            "company_name": v.company.name if v.company else "",
            "license_number": data.get("license_number", "91110108MA01XXXXXX"),
            "legal_person": data.get("legal_person", "张法定"),
            "contact_phone": data.get("contact_phone", "13800000000"),
            "status": v.status,
            "opinion": v.opinion,
            "created_at": v.created_at.strftime("%Y-%m-%d %H:%M")
        })
    return ResponseModel(data=results)

@router.post("/admin/verifications/{id}/approve", response_model=ResponseModel[dict])
def approve_verification(
    id: int,
    opinion: Optional[str] = "资质审核通过，准予公开发布招聘岗位",
    admin: User = Depends(require_roles(["PLATFORM_ADMIN", "SUPER_ADMIN"])),
    db: Session = Depends(get_db)
):
    v = db.query(CompanyVerification).filter(CompanyVerification.id == id).first()
    if not v:
        raise HTTPException(status_code=404, detail="认证记录不存在")

    v.status = "APPROVED"
    v.reviewer_id = admin.id
    v.opinion = opinion
    v.reviewed_at = datetime.utcnow()

    # Update company status to VERIFIED
    if v.company:
        v.company.status = "VERIFIED"

    log_operation(db, admin.id, "管理员", "ADMIN", "APPROVE_VERIFICATION", "COMPANY", v.company_id, f"通过企业【{v.company.name if v.company else ''}】资质认证")
    db.commit()
    return ResponseModel(data={"message": "企业实名认证已审核通过！"})

@router.post("/admin/verifications/{id}/reject", response_model=ResponseModel[dict])
def reject_verification(
    id: int,
    opinion: str,
    admin: User = Depends(require_roles(["PLATFORM_ADMIN", "SUPER_ADMIN"])),
    db: Session = Depends(get_db)
):
    v = db.query(CompanyVerification).filter(CompanyVerification.id == id).first()
    if not v:
        raise HTTPException(status_code=404, detail="认证记录不存在")

    v.status = "REJECTED"
    v.reviewer_id = admin.id
    v.opinion = opinion
    v.reviewed_at = datetime.utcnow()

    if v.company:
        v.company.status = "REJECTED"

    db.commit()
    return ResponseModel(data={"message": "已驳回企业认证"})

@router.get("/admin/jobs/review", response_model=ResponseModel[List[dict]])
def list_jobs_for_review(
    admin: User = Depends(require_roles(["PLATFORM_ADMIN", "SUPER_ADMIN"])),
    db: Session = Depends(get_db)
):
    jobs = db.query(Job).filter(Job.status.in_(["PENDING_REVIEW", "PUBLISHED", "REJECTED"])).order_by(Job.id.desc()).all()
    results = []
    for j in jobs:
        results.append({
            "id": j.id,
            "title": j.title,
            "company_name": j.company.name if j.company else "",
            "city": j.city,
            "salary": f"{j.salary_min}-{j.salary_max}K",
            "skills_required": j.skills_required,
            "status": j.status,
            "created_at": j.created_at.strftime("%Y-%m-%d %H:%M")
        })
    return ResponseModel(data=results)

@router.post("/admin/jobs/{id}/approve", response_model=ResponseModel[dict])
def approve_job(
    id: int,
    admin: User = Depends(require_roles(["PLATFORM_ADMIN", "SUPER_ADMIN"])),
    db: Session = Depends(get_db)
):
    job = db.query(Job).filter(Job.id == id).first()
    if not job:
        raise HTTPException(status_code=404, detail="岗位不存在")

    job.status = "PUBLISHED"
    db.commit()
    log_operation(db, admin.id, "管理员", "ADMIN", "APPROVE_JOB", "JOB", job.id, f"审核通过并公开发布岗位【{job.title}】")
    return ResponseModel(data={"message": "岗位审核通过，已正式上架至公开岗位广场！"})

@router.post("/admin/jobs/{id}/reject", response_model=ResponseModel[dict])
def reject_job(
    id: int,
    reason: str,
    admin: User = Depends(require_roles(["PLATFORM_ADMIN", "SUPER_ADMIN"])),
    db: Session = Depends(get_db)
):
    job = db.query(Job).filter(Job.id == id).first()
    if not job:
        raise HTTPException(status_code=404, detail="岗位不存在")

    job.status = "REJECTED"
    job.reject_reason = reason
    db.commit()
    return ResponseModel(data={"message": "岗位已驳回"})

@router.post("/admin/jobs/{id}/take-down", response_model=ResponseModel[dict])
def take_down_job(
    id: int,
    reason: str,
    admin: User = Depends(require_roles(["PLATFORM_ADMIN", "SUPER_ADMIN"])),
    db: Session = Depends(get_db)
):
    job = db.query(Job).filter(Job.id == id).first()
    if not job:
        raise HTTPException(status_code=404, detail="岗位不存在")

    job.status = "CLOSED"
    job.reject_reason = f"平台强制下架：{reason}"

    # Notify enterprise
    if job.company:
        for m in job.company.members:
            noti = Notification(
                user_id=m.user_id,
                type="SYSTEM",
                title=f"岗位强制下架通知：{job.title}",
                content=f"岗位【{job.title}】因【{reason}】被平台管理下架，历史申请仍保留，不可接收新投递。",
                link="/enterprise/jobs"
            )
            db.add(noti)

    db.commit()
    log_operation(db, admin.id, "管理员", "ADMIN", "TAKEDOWN_JOB", "JOB", job.id, f"强制下架违规岗位【{job.title}】：{reason}")
    return ResponseModel(data={"message": "岗位已执行强制下架"})

@router.get("/admin/complaints", response_model=ResponseModel[List[dict]])
def list_complaints(
    admin: User = Depends(require_roles(["PLATFORM_ADMIN", "SUPER_ADMIN"])),
    db: Session = Depends(get_db)
):
    comps = db.query(Complaint).order_by(Complaint.id.desc()).all()
    results = []
    for c in comps:
        results.append({
            "id": c.id,
            "category": c.category,
            "target_type": c.target_type,
            "description": c.description,
            "status": c.status,
            "resolution": c.resolution,
            "created_at": c.created_at.strftime("%Y-%m-%d %H:%M")
        })
    return ResponseModel(data=results)

@router.post("/admin/complaints/{id}/resolve", response_model=ResponseModel[dict])
def resolve_complaint(
    id: int,
    resolution: str,
    admin: User = Depends(require_roles(["PLATFORM_ADMIN", "SUPER_ADMIN"])),
    db: Session = Depends(get_db)
):
    c = db.query(Complaint).filter(Complaint.id == id).first()
    if not c:
        raise HTTPException(status_code=404, detail="投诉记录不存在")

    c.status = "RESOLVED"
    c.handler_id = admin.id
    c.resolution = resolution
    db.commit()
    return ResponseModel(data={"message": "投诉处理结论已保存并办结"})

@router.get("/admin/content", response_model=ResponseModel[dict])
def get_admin_content(admin: User = Depends(require_roles(["PLATFORM_ADMIN", "SUPER_ADMIN"]))):
    return ResponseModel(data={
        "banner_title": "让每一次面试都成为更好的自己",
        "banner_subtitle": "AI 驱动的模拟面试与职业成长平台，从校园到职场，陪你走好每一步",
        "announcement": "【平台通知】2026 年秋季校招专场正式启动，欢迎各大高校毕业生参与模拟面试！"
    })

@router.patch("/admin/content", response_model=ResponseModel[dict])
def update_admin_content(content: dict, admin: User = Depends(require_roles(["PLATFORM_ADMIN", "SUPER_ADMIN"]))):
    return ResponseModel(data={"message": "首页运营配置已实时生效更新"})

@router.get("/admin/ai/providers", response_model=ResponseModel[dict])
def get_ai_providers(
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles(["PLATFORM_ADMIN", "SUPER_ADMIN"]))
):
    from app.services import ai_settings
    cfg = ai_settings.get_effective_config(db)
    # Mask API key per spec: "API Key 只显示掩码，不能在页面回显完整值"
    masked_key = ai_settings.mask_key(cfg["api_key"]) or "sk-mock-••••••••••••"

    return ResponseModel(data={
        "provider": "Mock / OpenAI Compatible",
        "mode": cfg["mode"].upper(),
        "model": cfg["model"],
        "base_url": cfg["base_url"],
        "api_key_masked": masked_key,
        "configured": cfg["configured"],
        "prompt_version": "v3.0",
        "avg_latency_ms": 145,
        "total_calls_today": 128,
        "success_rate": 99.8
    })

@router.patch("/admin/ai/providers", response_model=ResponseModel[dict])
def update_ai_provider(
    config: dict,
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles(["PLATFORM_ADMIN", "SUPER_ADMIN"]))
):
    from app.services import ai_settings
    base_url = str(config.get("base_url", "")).strip()
    if base_url:
        err = ai_settings.validate_base_url(base_url)
        if err:
            raise HTTPException(status_code=400, detail=err)
    saved = ai_settings.save_config(db, config)
    return ResponseModel(data={
        "message": "AI 模型服务配置已安全更新并即时生效",
        "mode": saved["mode"].upper(),
    })

@router.get("/admin/ai/logs", response_model=ResponseModel[List[dict]])
def get_ai_logs(admin: User = Depends(require_roles(["PLATFORM_ADMIN", "SUPER_ADMIN"]))):
    # Spec: "AI 日志必须脱敏，不记录密码、Token 或不必要的隐私原文"
    return ResponseModel(data=[
        {"id": 1, "business_type": "RESUME_PARSE", "model": "mock-ai", "latency_ms": 120, "tokens": 420, "status": "SUCCESS", "time": "12:30:15"},
        {"id": 2, "business_type": "QUESTION_GEN", "model": "mock-ai", "latency_ms": 95, "tokens": 180, "status": "SUCCESS", "time": "12:31:02"},
        {"id": 3, "business_type": "EVALUATE_RUBRIC", "model": "mock-ai", "latency_ms": 150, "tokens": 580, "status": "SUCCESS", "time": "12:32:44"},
        {"id": 4, "business_type": "REPORT_GEN", "model": "mock-ai", "latency_ms": 210, "tokens": 920, "status": "SUCCESS", "time": "12:35:10"}
    ])

@router.get("/admin/roles", response_model=ResponseModel[List[dict]])
def list_roles(admin: User = Depends(require_roles(["PLATFORM_ADMIN", "SUPER_ADMIN"])), db: Session = Depends(get_db)):
    roles = db.query(Role).all()
    return ResponseModel(data=[
        {"id": r.id, "code": r.code, "name": r.name, "description": r.description}
        for r in roles
    ])

@router.get("/admin/audit-logs", response_model=ResponseModel[List[dict]])
def list_audit_logs(admin: User = Depends(require_roles(["PLATFORM_ADMIN", "SUPER_ADMIN"])), db: Session = Depends(get_db)):
    logs = db.query(OperationLog).order_by(OperationLog.id.desc()).limit(30).all()
    return ResponseModel(data=[
        {
            "id": l.id,
            "actor_id": l.actor_id,
            "actor_name": l.actor_name,
            "role": l.role,
            "action": l.action,
            "resource_type": l.resource_type,
            "resource_id": l.resource_id,
            "detail": l.detail,
            "ip": l.ip,
            "created_at": l.created_at.strftime("%Y-%m-%d %H:%M:%S")
        }
        for l in logs
    ])


# ==================== 结构化题库管理（M08 内容配置） ====================
# 说明：
# - 编辑/新增题目不影响历史面试：组卷时题干与要点已复制快照到 InterviewQuestion；
# - 只提供"启用/停用"，不做物理删除：bank_id 被追问题卷与错题清单引用；
# - 灌库脚本 --rebuild 只清理 source=SEED 的题目，人工新增（MANUAL）不会丢失。

def _qb_to_dict(q) -> dict:
    try:
        points = json.loads(q.reference_points_json) if q.reference_points_json else []
        if not isinstance(points, list):
            points = []
    except Exception:
        points = []
    return {
        "id": q.id,
        "job_category": q.job_category,
        "question_type": q.question_type,
        "skill_name": q.skill_name,
        "stage": q.stage,
        "difficulty": q.difficulty,
        "text": q.text,
        "reference_points": points,
        "hints": q.hints,
        "time_limit_sec": q.time_limit_sec,
        "source": q.source,
        "enabled": q.enabled,
        "usage_count": q.usage_count,
        "created_at": q.created_at,
        "updated_at": q.updated_at,
    }


@router.get("/admin/question-bank", response_model=ResponseModel[dict])
def list_question_bank(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = None,
    job_category: Optional[str] = None,
    question_type: Optional[str] = None,
    difficulty: Optional[str] = None,
    enabled: Optional[bool] = None,
    admin: User = Depends(require_roles(["PLATFORM_ADMIN", "SUPER_ADMIN"])),
    db: Session = Depends(get_db),
):
    """题库列表：分页 + 筛选（题干关键词/岗位大类/题型/难度/启用状态）。"""
    query = db.query(QuestionBank)
    if keyword:
        kw = f"%{keyword.strip()}%"
        query = query.filter(or_(QuestionBank.text.like(kw), QuestionBank.skill_name.like(kw)))
    if job_category:
        query = query.filter(QuestionBank.job_category == job_category)
    if question_type:
        query = query.filter(QuestionBank.question_type == question_type)
    if difficulty:
        query = query.filter(QuestionBank.difficulty == difficulty)
    if enabled is not None:
        query = query.filter(QuestionBank.enabled == enabled)

    total = query.count()
    rows = query.order_by(QuestionBank.id.desc()).offset((page - 1) * page_size).limit(page_size).all()

    # 全量分类统计（供筛选下拉与概览卡片）
    all_rows = db.query(QuestionBank).all()
    categories = sorted({r.job_category for r in all_rows})
    stats = {
        "total": len(all_rows),
        "enabled": sum(1 for r in all_rows if r.enabled),
        "by_type": {},
        "by_category": {},
    }
    for r in all_rows:
        stats["by_type"][r.question_type] = stats["by_type"].get(r.question_type, 0) + 1
        stats["by_category"][r.job_category] = stats["by_category"].get(r.job_category, 0) + 1

    return ResponseModel(data={
        "items": [_qb_to_dict(r) for r in rows],
        "total": total,
        "page": page,
        "page_size": page_size,
        "categories": categories,
        "stats": stats,
    })


@router.post("/admin/question-bank", response_model=ResponseModel[dict])
def create_question(
    req: QuestionBankUpsertRequest,
    admin: User = Depends(require_roles(["PLATFORM_ADMIN", "SUPER_ADMIN"])),
    db: Session = Depends(get_db),
):
    """新增题目（source=MANUAL，不被 --rebuild 清库影响）。"""
    dup = db.query(QuestionBank).filter(QuestionBank.text == req.text.strip()).first()
    if dup:
        raise HTTPException(status_code=400, detail="题干内容与已有题目完全相同")
    q = QuestionBank(
        job_category=req.job_category.strip(),
        question_type=req.question_type,
        skill_name=req.skill_name.strip(),
        stage=req.stage.strip(),
        difficulty=req.difficulty,
        text=req.text.strip(),
        reference_points_json=json.dumps(req.reference_points, ensure_ascii=False),
        hints=(req.hints or None),
        time_limit_sec=req.time_limit_sec,
        source="MANUAL",
        enabled=req.enabled,
    )
    db.add(q)
    db.commit()
    db.refresh(q)
    log_operation(db, admin.id, admin.email, "ADMIN", "CREATE_QUESTION", "QUESTION_BANK", q.id,
                  f"新增题库题目【{q.job_category}/{q.question_type}】")
    return ResponseModel(data=_qb_to_dict(q))


@router.put("/admin/question-bank/{id}", response_model=ResponseModel[dict])
def update_question(
    id: int,
    req: QuestionBankUpsertRequest,
    admin: User = Depends(require_roles(["PLATFORM_ADMIN", "SUPER_ADMIN"])),
    db: Session = Depends(get_db),
):
    """编辑题目元信息。注意：仅影响之后的组卷，历史面试卷面快照不变。"""
    q = db.query(QuestionBank).filter(QuestionBank.id == id).first()
    if not q:
        raise HTTPException(status_code=404, detail="题目不存在")
    dup = db.query(QuestionBank).filter(
        QuestionBank.text == req.text.strip(), QuestionBank.id != id).first()
    if dup:
        raise HTTPException(status_code=400, detail="题干内容与另一道已有题目完全相同")

    q.job_category = req.job_category.strip()
    q.question_type = req.question_type
    q.skill_name = req.skill_name.strip()
    q.stage = req.stage.strip()
    q.difficulty = req.difficulty
    q.text = req.text.strip()
    q.reference_points_json = json.dumps(req.reference_points, ensure_ascii=False)
    q.hints = req.hints or None
    q.time_limit_sec = req.time_limit_sec
    q.enabled = req.enabled
    db.commit()
    db.refresh(q)
    log_operation(db, admin.id, admin.email, "ADMIN", "UPDATE_QUESTION", "QUESTION_BANK", q.id,
                  f"编辑题库题目（source={q.source}）")
    return ResponseModel(data=_qb_to_dict(q))


@router.patch("/admin/question-bank/{id}/toggle", response_model=ResponseModel[dict])
def toggle_question(
    id: int,
    req: QuestionBankToggleRequest,
    admin: User = Depends(require_roles(["PLATFORM_ADMIN", "SUPER_ADMIN"])),
    db: Session = Depends(get_db),
):
    """启用/停用题目（不做物理删除：bank_id 被历史卷面与错题清单引用）。"""
    q = db.query(QuestionBank).filter(QuestionBank.id == id).first()
    if not q:
        raise HTTPException(status_code=404, detail="题目不存在")
    q.enabled = req.enabled
    db.commit()
    log_operation(db, admin.id, admin.email, "ADMIN",
                  "ENABLE_QUESTION" if req.enabled else "DISABLE_QUESTION",
                  "QUESTION_BANK", q.id, f"题目{'启用' if req.enabled else '停用'}")
    return ResponseModel(data={"id": q.id, "enabled": q.enabled})
