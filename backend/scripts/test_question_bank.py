"""题库组卷 + 状态机 + 自适应追问 端到端冒烟测试（临时 SQLite，AI 走 mock 通道）。"""
import os
import sys
import json
import tempfile

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND)

TMP_DB = os.path.join(tempfile.gettempdir(), "qb_smoke.db")
if os.path.exists(TMP_DB):
    os.remove(TMP_DB)
os.environ["DATABASE_URL"] = f"sqlite:///{TMP_DB}"
# 冒烟测试走 mock 评分通道：结果确定、不依赖外网与配额
os.environ["AI_MODE"] = "mock"

from fastapi.testclient import TestClient  # noqa: E402
import main  # noqa: E402
from app.core.database import SessionLocal  # noqa: E402
from app.models.question import QuestionBank  # noqa: E402
from app.models.interview import Interview, InterviewQuestion, InterviewPlan  # noqa: E402
from app.models.job import Job, JobSkill  # noqa: E402
from app.models.user import User, UserRole  # noqa: E402
from app.models.company import Company  # noqa: E402
from app.core.security import get_password_hash  # noqa: E402
from scripts.seed_question_bank import seed_question_bank  # noqa: E402

PASS, FAIL = [], []


def check(name, cond, extra=""):
    (PASS if cond else FAIL).append(name)
    print(f"{'PASS' if cond else 'FAIL'}: {name} {extra}")


GOOD_ANS = "我在电商项目中用 Redis 做热点缓存，采用 Cache Aside 模式：写时先更新数据库再删除缓存，" \
           "并用延迟双删与 Canal 订阅 binlog 兜底，配合布隆过滤器防穿透，逻辑过期防击穿，TTL 加随机抖动防雪崩。"
BAD_ANS = "不知道，没用过。"

db = SessionLocal()
stat = seed_question_bank(db)
db.commit()
check("题库灌库", stat["total"] >= 80, f"total={stat['total']}")
stat2 = seed_question_bank(db)
db.commit()
check("灌库幂等（第二次不新增）", stat2["inserted"] == 0 and stat2["total"] == stat["total"])

company = Company(name="测试科技", industry="互联网/软件", size="150-500人",
                  city="深圳", status="VERIFIED")
db.add(company); db.commit(); db.refresh(company)
job = Job(company_id=company.id, title="Java后端开发工程师", category="后端开发", city="深圳",
          description="d", duties="du", requirements="re", skills_required="Java,MySQL,Redis",
          status="PUBLISHED")
db.add(job); db.commit(); db.refresh(job)
for s in ["Java", "MySQL", "Redis"]:
    db.add(JobSkill(job_id=job.id, skill_name=s, level="熟练", required=True))

user = User(email="qb_test@example.com", phone="13900000099",
            password_hash=get_password_hash("123456"), account_type="PERSONAL", status="ACTIVE")
db.add(user); db.commit(); db.refresh(user)
db.add(UserRole(user_id=user.id, role_code="PERSONAL_USER"))
db.commit()

JOB_ID = job.id

# 找一道 Redis MEDIUM 题用于确定性追问测试
redis_medium = db.query(QuestionBank).filter(
    QuestionBank.skill_name == "Redis", QuestionBank.difficulty == "MEDIUM").first()
REDIS_M_ID = redis_medium.id if redis_medium else None
redis_hard_cnt = db.query(QuestionBank).filter(
    QuestionBank.skill_name == "Redis", QuestionBank.difficulty == "HARD").count()
db.close()

client = TestClient(main.app)
login = client.post("/api/v1/auth/login", json={"account": "qb_test@example.com", "password": "123456"})
check("登录", login.status_code == 200, str(login.status_code))
token = login.json()["data"]["access_token"]
H = {"Authorization": f"Bearer {token}"}

# ===== 1. 题库/配比/预览 =====
r = client.get("/api/v1/interviews/bank-stats", headers=H)
check("bank-stats 接口", r.status_code == 200 and r.json()["data"]["ready"])
r = client.get("/api/v1/interviews/paper-ratio", params={"mode": "COMPREHENSIVE", "total_questions": 10}, headers=H)
d = r.json()["data"]
check("5:3:2 配比分配 10 题", d["allocated"] == {"PROFESSIONAL": 5, "GENERAL": 3, "STRESS": 2}, str(d["allocated"]))

r = client.post("/api/v1/interviews/paper-preview",
                json={"job_id": JOB_ID, "mode": "COMPREHENSIVE", "difficulty": "MEDIUM", "total_questions": 5},
                headers=H)
prev = r.json()["data"]
check("组卷预览返回 5 题", len(prev["questions"]) == 5)
picked_ids = [q["bank_id"] for q in prev["questions"] if q["bank_id"]]

# ===== 2. 创建面试（完整链路：答完自动结算） =====
# 首题固定为 Redis MEDIUM，保证 mock DEEP 评分能命中同技能 HARD 题触发追问
init_ids = [REDIS_M_ID] if REDIS_M_ID else None
r = client.post("/api/v1/interviews",
                json={"job_id": JOB_ID, "mode": "COMPREHENSIVE", "difficulty": "MEDIUM",
                      "total_questions": 5, "duration_minutes": 25,
                      "selected_bank_ids": init_ids},
                headers=H)
check("创建面试", r.status_code == 200)
iv = r.json()["data"]
iv_id = iv["id"]
qs = iv["questions"]
check("卷面预生成全部 5 题", len(qs) == 5)
check("闭卷：作答阶段不下发参考答案", all(not q["reference_points"] for q in qs))

# start → 状态机 + 服务端剩余时间
r = client.post(f"/api/v1/interviews/{iv_id}/start", headers=H)
check("start 返回服务端剩余时间",
      r.status_code == 200 and isinstance(r.json()["data"].get("remaining_seconds"), int))
r2 = client.post(f"/api/v1/interviews/{iv_id}/start", headers=H)
check("重复 start → 409", r2.status_code == 409, str(r2.status_code))

# 逐题作答直到服务端判定完成（mock 高分答案会触发 DEEP 追问，总题数可能 +1/+2）
answered = 0
followup_seen = False
finished = False
for _ in range(10):
    r = client.post(f"/api/v1/interviews/{iv_id}/answer",
                    json={"text": GOOD_ANS, "duration_sec": 90}, headers=H)
    if r.status_code != 200:
        check(f"第{answered+1}题作答", False, str(r.status_code) + r.text[:120])
        break
    d = r.json()["data"]
    answered += 1
    if d.get("is_followup"):
        followup_seen = True
    if d.get("is_finished"):
        check("最后一题作答返回 report_id（自动结算）", d.get("report_id") is not None)
        finished = True
        break
    nq = d.get("next_question")
    check(f"第{answered}题下一题闭卷", nq is None or not nq.get("reference_points"))
check("答完全部题目（含追问）自动完成", finished, f"answered={answered}")
check("mock 高分触发自适应追问（DEEP→同技能更高难度）", followup_seen)

r = client.get(f"/api/v1/interviews/{iv_id}", headers=H)
iv_after = r.json()["data"]
check("追问后总题数增加且等于作答数", iv_after["total_questions"] == answered,
      f"total={iv_after['total_questions']} answered={answered}")
check("answered_count 真实", iv_after.get("answered_count") == answered)
seqs = [q["seq"] for q in iv_after["questions"]]
check("seq 连续无重复", seqs == list(range(1, len(seqs) + 1)), str(seqs))
db = SessionLocal()
plan = db.query(InterviewPlan).filter(InterviewPlan.interview_id == iv_id).first()
snap = json.loads(plan.paper_json) if plan and plan.paper_json else {}
check("卷面快照 followup_count>0", snap.get("followup_count", 0) > 0, str(snap.get("followup_count")))
db.close()

# 结算后操作全部 409
r = client.post(f"/api/v1/interviews/{iv_id}/answer", json={"text": GOOD_ANS, "duration_sec": 30}, headers=H)
check("结算后再作答 → 409", r.status_code == 409, str(r.status_code))
r = client.post(f"/api/v1/interviews/{iv_id}/abort", headers=H)
check("终态再中止 → 409", r.status_code == 409, str(r.status_code))
r = client.post(f"/api/v1/interviews/{iv_id}/finish", headers=H)
check("finish 幂等（返回既有报告）", r.status_code == 200)

# 报告
r = client.get(f"/api/v1/interviews/{iv_id}/report", headers=H)
check("获取报告", r.status_code == 200)
qa = r.json()["data"]["questions_analysis"]
check("报告逐题数=作答数", len(qa) == answered, f"got={len(qa)}")
check("报告逐题含参考答案要点", all(len(x.get("reference_points", [])) > 0 for x in qa))
r = client.get(f"/api/v1/interviews/{iv_id}", headers=H)
check("结束后可见参考答案（复盘对照）",
      all(q["reference_points"] for q in r.json()["data"]["questions"]))

# ===== 3. 中止流程 =====
r = client.post("/api/v1/interviews",
                json={"job_id": JOB_ID, "mode": "COMPREHENSIVE", "difficulty": "MEDIUM", "total_questions": 3},
                headers=H)
iv_ab = r.json()["data"]
client.post(f"/api/v1/interviews/{iv_ab['id']}/start", headers=H)
r = client.post(f"/api/v1/interviews/{iv_ab['id']}/abort", headers=H)
check("abort 成功 → CANCELLED", r.status_code == 200 and r.json()["data"]["status"] == "CANCELLED")
r = client.get(f"/api/v1/interviews/{iv_ab['id']}/report", headers=H)
check("中止后无报告 → 404（不再返回假报告）", r.status_code == 404, str(r.status_code))
r = client.post(f"/api/v1/interviews/{iv_ab['id']}/answer", json={"text": "x", "duration_sec": 5}, headers=H)
check("中止后作答 → 409", r.status_code == 409, str(r.status_code))
r = client.post(f"/api/v1/interviews/{iv_ab['id']}/finish", headers=H)
check("中止后交卷 → 409", r.status_code == 409, str(r.status_code))

# ===== 4. 未答完 finish 拦截（force 提前交卷除外路径） =====
r = client.post("/api/v1/interviews",
                json={"job_id": JOB_ID, "mode": "COMPREHENSIVE", "difficulty": "MEDIUM", "total_questions": 3},
                headers=H)
iv_p = r.json()["data"]
client.post(f"/api/v1/interviews/{iv_p['id']}/start", headers=H)
client.post(f"/api/v1/interviews/{iv_p['id']}/answer", json={"text": BAD_ANS, "duration_sec": 10}, headers=H)
# REST finish 是"提前交卷"语义（force=True），应成功且只统计已答题
r = client.post(f"/api/v1/interviews/{iv_p['id']}/finish", headers=H)
check("提前交卷成功（已答1题也可出报告）", r.status_code == 200, str(r.status_code) + r.text[:100])
r = client.get(f"/api/v1/interviews/{iv_p['id']}/report", headers=H)
check("提前交卷报告只含已答题", r.status_code == 200 and len(r.json()["data"]["questions_analysis"]) == 1)

# 完全无作答 finish → 409
r = client.post("/api/v1/interviews",
                json={"job_id": JOB_ID, "mode": "COMPREHENSIVE", "difficulty": "MEDIUM", "total_questions": 3},
                headers=H)
iv_e = r.json()["data"]
r = client.post(f"/api/v1/interviews/{iv_e['id']}/finish", headers=H)
check("无作答交卷 → 409（不再产出写死82分假报告）", r.status_code == 409, str(r.status_code))
r = client.get("/api/v1/interviews", headers=H)
lst = {x["id"]: x for x in r.json()["data"]}
check("列表无报告 score=None（不写死82）", lst[iv_e["id"]]["score"] is None)

# ===== 5. 关闭题库走 AI 全量生成 =====
r = client.post("/api/v1/interviews",
                json={"job_id": JOB_ID, "mode": "TECHNICAL", "difficulty": "HARD",
                      "total_questions": 3, "use_question_bank": False},
                headers=H)
iv2 = r.json()["data"]
check("关闭题库走 AI 生成", all(q["source"] == "AI_GENERATED" for q in iv2["questions"]))

# ===== 6. 所见即所考 =====
r = client.post("/api/v1/interviews/paper-preview",
                json={"job_id": JOB_ID, "mode": "COMPREHENSIVE", "difficulty": "MEDIUM", "total_questions": 5},
                headers=H)
picked = r.json()["data"]
p_ids = [q["bank_id"] for q in picked["questions"] if q["bank_id"]]
r = client.post("/api/v1/interviews",
                json={"job_id": JOB_ID, "mode": "COMPREHENSIVE", "difficulty": "MEDIUM",
                      "total_questions": 5, "selected_bank_ids": p_ids},
                headers=H)
iv3 = r.json()["data"]
check("所见即所考",
      {q["text"] for q in iv3["questions"]} == {q["text"] for q in picked["questions"]})

# ===== 7. 低质量答案触发降难追问（BASIC/SIMPLIFY） =====
if REDIS_M_ID and redis_hard_cnt >= 1:
    # 用固定 Redis MEDIUM 作为首题
    r = client.post("/api/v1/interviews",
                    json={"job_id": JOB_ID, "mode": "COMPREHENSIVE", "difficulty": "MEDIUM",
                          "total_questions": 2, "selected_bank_ids": [REDIS_M_ID]},
                    headers=H)
    iv4 = r.json()["data"]
    first_q = [q for q in iv4["questions"] if q["seq"] == 1][0]
    check("首题为指定 Redis 题", first_q["skill_name"] == "Redis", first_q["skill_name"])
    client.post(f"/api/v1/interviews/{iv4['id']}/start", headers=H)
    r = client.post(f"/api/v1/interviews/{iv4['id']}/answer",
                    json={"text": BAD_ANS, "duration_sec": 10}, headers=H)
    d = r.json()["data"]
    check("低质量答案触发降难追问题", d.get("is_followup") is True,
          f"next={d.get('next_question', {}).get('difficulty') if d.get('next_question') else None}")
    # 追问题应为 EASY（降难）
    if d.get("next_question"):
        check("追问题难度下调", d["next_question"]["difficulty"] == "EASY", d["next_question"]["difficulty"])

print("\n" + "=" * 60)
print(f"RESULT: {len(PASS)} passed, {len(FAIL)} failed")
if FAIL:
    print("FAILED:", FAIL)
    sys.exit(1)
print("ALL CHECKS PASSED")
