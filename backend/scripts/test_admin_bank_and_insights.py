"""题库管理（B8）+ 历史对比/薄弱题重练（B9）端到端冒烟测试。"""
import os
import sys
import json
import tempfile

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND)

TMP_DB = os.path.join(tempfile.gettempdir(), "qb_admin_smoke.db")
if os.path.exists(TMP_DB):
    os.remove(TMP_DB)
os.environ["DATABASE_URL"] = f"sqlite:///{TMP_DB}"
os.environ["AI_MODE"] = "mock"

from fastapi.testclient import TestClient  # noqa: E402
import main  # noqa: E402
from app.core.database import SessionLocal  # noqa: E402
from app.models.question import QuestionBank  # noqa: E402
from app.models.job import Job, JobSkill  # noqa: E402
from app.models.user import User, UserRole  # noqa: E402
from app.models.company import Company  # noqa: E402
from app.core.security import get_password_hash  # noqa: E402
from scripts.seed_question_bank import seed_question_bank  # noqa: E402

PASS, FAIL = [], []


def check(name, cond, extra=""):
    (PASS if cond else FAIL).append(name)
    print(f"{'PASS' if cond else 'FAIL'}: {name} {extra}")


db = SessionLocal()
seed_question_bank(db)
company = Company(name="测试科技", industry="互联网/软件", size="150-500人",
                  city="深圳", status="VERIFIED")
db.add(company); db.commit(); db.refresh(company)
job = Job(company_id=company.id, title="Java后端开发工程师", category="后端开发", city="深圳",
          description="d", duties="du", requirements="re", skills_required="Java,MySQL,Redis",
          status="PUBLISHED")
db.add(job); db.commit(); db.refresh(job)
db.add(JobSkill(job_id=job.id, skill_name="Redis", level="熟练", required=True))

student = User(email="stu@example.com", password_hash=get_password_hash("123456"),
               account_type="PERSONAL", status="ACTIVE")
admin = User(email="admin@example.com", password_hash=get_password_hash("123456"),
             account_type="ADMIN", status="ACTIVE")
normal_admin = User(email="padmin@example.com", password_hash=get_password_hash("123456"),
                    account_type="ADMIN", status="ACTIVE")
db.add_all([student, admin, normal_admin]); db.commit(); db.refresh(student)
db.add_all([
    UserRole(user_id=student.id, role_code="PERSONAL_USER"),
    UserRole(user_id=admin.id, role_code="SUPER_ADMIN"),
    UserRole(user_id=normal_admin.id, role_code="PLATFORM_ADMIN"),
])
db.commit()
JOB_ID = job.id
db.close()

client = TestClient(main.app)


def login(account):
    r = client.post("/api/v1/auth/login", json={"account": account, "password": "123456"})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['data']['access_token']}"}


H_ADMIN = login("admin@example.com")
H_PADMIN = login("padmin@example.com")
H_STU = login("stu@example.com")

# ===== 1. 权限控制 =====
r = client.get("/api/v1/admin/question-bank", headers=H_STU)
check("个人用户访问题库管理被拒", r.status_code in (401, 403), str(r.status_code))
r = client.get("/api/v1/admin/question-bank", headers=H_PADMIN)
check("平台管理员可访问题库管理", r.status_code == 200, str(r.status_code))
r = client.get("/api/v1/admin/question-bank")
check("未登录访问被拒", r.status_code in (401, 403), str(r.status_code))

# ===== 2. 列表/筛选/统计 =====
r = client.get("/api/v1/admin/question-bank", params={"page": 1, "page_size": 20}, headers=H_ADMIN)
d = r.json()["data"]
check("列表分页返回", d["total"] >= 86 and len(d["items"]) == 20)
check("分类统计存在", d["stats"]["by_type"].get("STRESS", 0) >= 12 and len(d["categories"]) >= 10)
r = client.get("/api/v1/admin/question-bank",
               params={"question_type": "STRESS", "page_size": 100}, headers=H_ADMIN)
d2 = r.json()["data"]
check("按题型筛选", all(i["question_type"] == "STRESS" for i in d2["items"]) and d2["total"] >= 12)
r = client.get("/api/v1/admin/question-bank", params={"keyword": "Redis"}, headers=H_ADMIN)
check("关键词搜索", r.json()["data"]["total"] >= 3, str(r.json()["data"]["total"]))

# ===== 3. 新增 / 编辑 / 停用 =====
new_payload = {
    "job_category": "后端开发", "question_type": "PROFESSIONAL", "skill_name": "Kafka",
    "stage": "专业基础", "difficulty": "MEDIUM",
    "text": "【测试题】请说明 Kafka 如何保证消息不丢失，以及 ISR 与 acks 配置的关系。",
    "reference_points": ["生产端 acks=all + 重试", "Broker 副本与 min.insync.replicas", "消费端手动提交 offset"],
    "hints": "按生产、存储、消费三段作答", "time_limit_sec": 180, "enabled": True
}
r = client.post("/api/v1/admin/question-bank", json=new_payload, headers=H_ADMIN)
check("新增题目成功", r.status_code == 200, str(r.status_code) + r.text[:100])
qid = r.json()["data"]["id"]
check("新题 source=MANUAL", r.json()["data"]["source"] == "MANUAL")

r = client.post("/api/v1/admin/question-bank", json=new_payload, headers=H_ADMIN)
check("题干完全相同被拒", r.status_code == 400, str(r.status_code))

bad = dict(new_payload, text="短", question_type="WRONG")
r = client.post("/api/v1/admin/question-bank", json=bad, headers=H_ADMIN)
check("非法题型/短题干被拒(422)", r.status_code == 422, str(r.status_code))

upd = dict(new_payload, difficulty="HARD", time_limit_sec=240)
r = client.put(f"/api/v1/admin/question-bank/{qid}", json=upd, headers=H_ADMIN)
check("编辑题目成功", r.status_code == 200 and r.json()["data"]["difficulty"] == "HARD")

r = client.patch(f"/api/v1/admin/question-bank/{qid}/toggle", json={"enabled": False}, headers=H_ADMIN)
check("停用题目成功", r.status_code == 200 and r.json()["data"]["enabled"] is False)
r = client.get("/api/v1/admin/question-bank", params={"enabled": False}, headers=H_ADMIN)
check("停用列表可查", any(i["id"] == qid for i in r.json()["data"]["items"]))

# 停用题不参与组卷
r = client.post("/api/v1/interviews", json={
    "job_id": JOB_ID, "mode": "COMPREHENSIVE", "difficulty": "MEDIUM",
    "total_questions": 5, "selected_bank_ids": [qid]}, headers=H_STU)
iv = r.json()["data"]
check("停用题不出现在卷面", all(q["bank_id"] != qid for q in iv["questions"])
      if all("bank_id" in q for q in iv["questions"]) else True)
texts = {q["text"] for q in iv["questions"]}
check("停用题题干不在卷面", new_payload["text"] not in texts)

# ===== 4. 薄弱题清单与重练 =====
r = client.get("/api/v1/interviews/weak-questions", headers=H_STU)
check("无作答时薄弱清单为空态", r.status_code == 200 and r.json()["data"]["weak_count"] == 0)

# 造一段"差生"面试：BAD 答案触发低分
BAD = "不知道，没用过。"
r = client.post("/api/v1/interviews", json={
    "job_id": JOB_ID, "mode": "TECHNICAL", "difficulty": "MEDIUM", "total_questions": 3},
    headers=H_STU)
iv_id = r.json()["data"]["id"]
client.post(f"/api/v1/interviews/{iv_id}/start", headers=H_STU)
for _ in range(6):
    d = client.post(f"/api/v1/interviews/{iv_id}/answer",
                    json={"text": BAD, "duration_sec": 20}, headers=H_STU).json()["data"]
    if d.get("is_finished"):
        break

r = client.get("/api/v1/interviews/weak-questions", params={"threshold": 60}, headers=H_STU)
wk = r.json()["data"]
check("低分作答进入薄弱清单", wk["weak_count"] >= 1, f"weak={wk['weak_count']}")
check("薄弱题含 bank_id 与得分", all("bank_id" in w and "latest_score" in w for w in wk["items"]))
check("薄弱题可重练 ID 列表", len(wk["retrain_bank_ids"]) == wk["weak_count"])

# 重练创建：purpose=RETRAIN，卷面即薄弱题（带 job_id 以便验证 include_retrain 口径）
r = client.post("/api/v1/interviews", json={
    "job_id": JOB_ID, "mode": "COMPREHENSIVE", "difficulty": "MEDIUM",
    "total_questions": min(2, len(wk["retrain_bank_ids"])),
    "selected_bank_ids": wk["retrain_bank_ids"][:2], "purpose": "RETRAIN"},
    headers=H_STU)
check("重练面试创建成功", r.status_code == 200, str(r.status_code))
retrain_iv = r.json()["data"]
weak_texts = {w["text"] for w in wk["items"]}
check("重练卷面=薄弱题本身", all(q["text"] in weak_texts for q in retrain_iv["questions"]),
      str([q["text"][:12] for q in retrain_iv["questions"]]))

db = SessionLocal()
from app.models.interview import Interview
iv_row = db.query(Interview).filter(Interview.id == retrain_iv["id"]).first()
check("purpose 落库 RETRAIN", iv_row.purpose == "RETRAIN")
db.close()

# 列表接口带 purpose 字段
r = client.get("/api/v1/interviews", headers=H_STU)
lst = r.json()["data"]
check("列表含 purpose 字段", any(x.get("purpose") == "RETRAIN" for x in lst))

# ===== 5. 历史对比 =====
r = client.get("/api/v1/interviews/history-comparison", headers=H_STU)
cmp1 = r.json()["data"]
check("1 次面试时对比不就绪（空态）", cmp1["ready"] is False and "至少" in (cmp1.get("message") or ""),
      str(cmp1.get("message")))

# 再完成一次同岗位 NORMAL 面试
r = client.post("/api/v1/interviews", json={
    "job_id": JOB_ID, "mode": "TECHNICAL", "difficulty": "MEDIUM", "total_questions": 2},
    headers=H_STU)
iv2_id = r.json()["data"]["id"]
client.post(f"/api/v1/interviews/{iv2_id}/start", headers=H_STU)
for _ in range(5):
    d = client.post(f"/api/v1/interviews/{iv2_id}/answer",
                    json={"text": BAD, "duration_sec": 20}, headers=H_STU).json()["data"]
    if d.get("is_finished"):
        break

r = client.get("/api/v1/interviews/history-comparison", params={"job_id": JOB_ID}, headers=H_STU)
cmp2 = r.json()["data"]
check("2 次面试后对比就绪", cmp2["ready"] is True, f"sessions={cmp2.get('session_count')}")
check("逐维趋势含 delta", all("delta" in v and "series" in v for v in cmp2["dimension_trends"].values()))
check("默认排除 RETRAIN", cmp2["session_count"] == 2, str(cmp2["session_count"]))

# 把重练也答完，然后 include_retrain=True 应包含 3 次
for _ in range(5):
    d = client.post(f"/api/v1/interviews/{retrain_iv['id']}/answer",
                    json={"text": BAD, "duration_sec": 20}, headers=H_STU).json()["data"]
    if d.get("is_finished"):
        break
r = client.get("/api/v1/interviews/history-comparison",
               params={"job_id": JOB_ID, "include_retrain": True}, headers=H_STU)
cmp3 = r.json()["data"]
check("include_retrain 含 3 次", cmp3["ready"] is True and cmp3["session_count"] == 3,
      str(cmp3.get("session_count")))

# ===== 6. 成长中心不再写死兜底 =====
r = client.get("/api/v1/personal/growth", headers=H_STU)
g = r.json()["data"]
check("growth 真实趋势", g["interview_count"] >= 2 and g["score_trend"], f"count={g['interview_count']}")
check("growth 默认排除重练", all(
    not (t.get("interview_id") == retrain_iv["id"]) for t in g["score_trend"]))
r = client.get("/api/v1/personal/growth", params={"include_retrain": True}, headers=H_STU)
g2 = r.json()["data"]
check("growth include_retrain 含重练", any(
    t.get("interview_id") == retrain_iv["id"] for t in g2["score_trend"]))

fresh = User(email="fresh@example.com", password_hash=get_password_hash("123456"),
             account_type="PERSONAL", status="ACTIVE")
db = SessionLocal(); db.add(fresh); db.commit(); db.close()
H_FRESH = login("fresh@example.com")
r = client.get("/api/v1/personal/growth", headers=H_FRESH)
gf = r.json()["data"]
check("新用户 growth 空态（无假 68/74/82）",
      gf["has_data"] is False and gf["score_trend"] == [] and gf["avg_score"] is None
      and gf["completed_tasks_rate"] is None, str(gf["score_trend"]))

print("\n" + "=" * 60)
print(f"RESULT: {len(PASS)} passed, {len(FAIL)} failed")
if FAIL:
    print("FAILED:", FAIL)
    sys.exit(1)
print("ALL CHECKS PASSED")
