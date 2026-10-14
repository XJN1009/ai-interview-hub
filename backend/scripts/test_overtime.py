"""单题服务端超时校验（B6）端到端冒烟测试。

D4 决策：修复并纳入回归。此前脚本仍按「无 question_id / 无 request_id / 末题自动结算」
的旧契约调用，接口 422 后整条超时链路处于零自动化覆盖状态。现按现行契约重写：
- 作答必须携带服务端下发的当前题 question_id 与幂等 request_id；
- 末题答完进入反问环节（phase=REVERSE），需跳过反问后再交卷才有报告；
- 整场不限制提交时间（D6），脚本只验证单题超时口径，不再假设整场归零。
"""
import os
import sys
import uuid
import tempfile
from datetime import datetime, timedelta

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND)

TMP_DB = os.path.join(tempfile.gettempdir(), "overtime_smoke.db")
if os.path.exists(TMP_DB):
    os.remove(TMP_DB)
os.environ["DATABASE_URL"] = f"sqlite:///{TMP_DB}"
os.environ["AI_MODE"] = "mock"

from fastapi.testclient import TestClient  # noqa: E402
import main  # noqa: E402
from app.core.database import SessionLocal  # noqa: E402
from app.models.interview import Interview, InterviewAnswer, InterviewQuestion  # noqa: E402
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
user = User(email="ot@example.com", password_hash=get_password_hash("123456"),
            account_type="PERSONAL", status="ACTIVE")
db.add(user); db.commit(); db.refresh(user)
db.add(UserRole(user_id=user.id, role_code="PERSONAL_USER"))
db.commit()
JOB_ID = job.id
db.close()

client = TestClient(main.app)
r = client.post("/api/v1/auth/login", json={"account": "ot@example.com", "password": "123456"})
H = {"Authorization": f"Bearer {r.json()['data']['access_token']}"}
check("登录", r.status_code == 200)

GOOD = "我在电商项目中用 Redis 做热点缓存，采用 Cache Aside 模式：写时先更新数据库再删除缓存，" \
       "并用延迟双删与 Canal 订阅 binlog 兜底，配合布隆过滤器防穿透，逻辑过期防击穿，TTL 加随机抖动防雪崩。"


def create_interview(qcount=2):
    rr = client.post("/api/v1/interviews", json={
        "job_id": JOB_ID, "mode": "TECHNICAL", "difficulty": "MEDIUM",
        "total_questions": qcount, "duration_minutes": 30}, headers=H)
    d = rr.json()["data"]
    return d["id"], d["questions"]


def current_qid(iv_id):
    """从面试详情取服务端当前作答题目 ID（追问插题后卷面会移位，不能按 seq 硬取）。"""
    detail = client.get(f"/api/v1/interviews/{iv_id}", headers=H).json()["data"]
    curr = detail.get("current_question")
    return curr["id"] if curr else None


def answer(iv_id, text, duration_sec=90, question_id=None):
    """现行契约：必须携带 question_id 与幂等 request_id。"""
    qid = question_id if question_id is not None else current_qid(iv_id)
    if qid is None:
        return None
    return client.post(f"/api/v1/interviews/{iv_id}/answer",
                       json={"question_id": qid, "request_id": uuid.uuid4().hex,
                             "text": text, "duration_sec": duration_sec}, headers=H)


# ===== 1. 创建即写入单题呈现锚点 =====
iv_id, qs = create_interview(2)
db = SessionLocal()
iv = db.query(Interview).filter(Interview.id == iv_id).first()
check("创建面试即写入 current_question_shown_at", iv.current_question_shown_at is not None)
db.close()

client.post(f"/api/v1/interviews/{iv_id}/start", headers=H)

# ===== 2. 正常时限内作答：不超时、不扣分 =====
d1 = answer(iv_id, GOOD, duration_sec=999).json()["data"]
check("时限内作答不标记超时", d1["overtime"] is False, f"overtime_sec={d1['overtime_sec']}")
check("服务端用时覆盖客户端上报（999 被纠正）", 0 < d1.get("raw_score", 0) <= 100)
db = SessionLocal()
ans1 = db.query(InterviewAnswer).filter(InterviewAnswer.interview_id == iv_id).order_by(
    InterviewAnswer.id.asc()).first()
check("落库 duration_sec 为服务端口径（远小于 999）", ans1.duration_sec < 60, f"got={ans1.duration_sec}")
check("落库 overtime=False", ans1.overtime is False)
db.close()

# ===== 3. 推进下一题后锚点重置 =====
db = SessionLocal()
iv = db.query(Interview).filter(Interview.id == iv_id).first()
check("推进后锚点刷新到新题", iv.current_question_shown_at is not None
      and iv.current_question_seq == 2)
db.close()

# ===== 4. 人为把锚点拨回过去 → 触发超时轻扣分 =====
qid2 = current_qid(iv_id)
db = SessionLocal()
q2 = db.get(InterviewQuestion, qid2)
LIMIT = q2.time_limit_sec or 180
iv = db.query(Interview).filter(Interview.id == iv_id).first()
iv.current_question_shown_at = datetime.utcnow() - timedelta(seconds=LIMIT + 100)
db.commit()
db.close()

d2 = answer(iv_id, GOOD, duration_sec=5).json()["data"]
check("超时被服务端标记", d2["overtime"] is True, f"overtime_sec={d2['overtime_sec']}")
check("超时秒数正确（约 100s）", 95 <= d2["overtime_sec"] <= 130, str(d2["overtime_sec"]))
check("超时轻扣分：最终分低于原始分", d2["total_score"] < d2["raw_score"],
      f"raw={d2['raw_score']} final={d2['total_score']}")
check("超时扣分上限 15 分且不归零",
      (d2["raw_score"] - d2["total_score"]) <= 15.0 and d2["total_score"] > 0,
      f"penalty={round(d2['raw_score'] - d2['total_score'], 1)}")
check("超时说明进入 evidence", any("超时" in e or "限时" in e for e in d2["evidence"]))

# ===== 5. 空作答：0 分 + 明确提示 =====
iv3_id, _ = create_interview(1)
client.post(f"/api/v1/interviews/{iv3_id}/start", headers=H)
d3 = answer(iv3_id, "   ", duration_sec=10).json()["data"]
check("空作答得 0 分", d3["total_score"] == 0.0, str(d3["total_score"]))
check("空作答标记 is_empty", d3.get("is_empty") is True)
check("空作答给出留白提示", any("留白" in s or "空作答" in w + s
                           for s in d3["suggestions"] for w in d3["weaknesses"])
      or any("空作答" in w for w in d3["weaknesses"]), str(d3["weaknesses"])[:60])
check("空作答不叠加超时扣分", d3["overtime"] is False or d3["total_score"] == 0.0)

# ===== 6. 暂停时长不计入单题用时 =====
iv4_id, _ = create_interview(1)
client.post(f"/api/v1/interviews/{iv4_id}/start", headers=H)
db = SessionLocal()
iv4 = db.query(Interview).filter(Interview.id == iv4_id).first()
q4 = db.get(InterviewQuestion, current_qid(iv4_id))
lim4 = q4.time_limit_sec or 180
# 锚点拨到超时前 5 秒，并模拟暂停 600 秒
iv4.current_question_shown_at = datetime.utcnow() - timedelta(seconds=lim4 - 5)
iv4.paused_at = datetime.utcnow() - timedelta(seconds=600)
iv4.status = "PAUSED"
db.commit(); db.close()
client.post(f"/api/v1/interviews/{iv4_id}/resume", headers=H)
d4 = answer(iv4_id, GOOD, duration_sec=5).json()["data"]
check("暂停 600 秒后恢复不算超时", d4["overtime"] is False,
      f"overtime_sec={d4['overtime_sec']}")

# ===== 7. 末题答完进入反问环节，跳过反问后才交卷出报告 =====
# mock 高分答案会触发 DEEP 追问扩卷，需循环答到服务端判定完成
answered_count = 2
last = d2
while not last.get("is_finished") and answered_count < 8:
    nxt = answer(iv_id, GOOD, duration_sec=5)
    if nxt is None:
        break
    last = nxt.json()["data"]
    answered_count += 1
check("逐题作答已答完", last.get("is_finished") is True, f"answered={answered_count}")
check("答完进入反问环节（不再自动结算）", last.get("phase") == "REVERSE", str(last.get("phase")))
check("答完时不返回报告 ID", last.get("report_id") is None)

skip = client.post(f"/api/v1/interviews/{iv_id}/reverse/skip", headers=H)
check("跳过反问成功", skip.status_code == 200 and skip.json()["data"]["phase"] == "DONE",
      str(skip.status_code))
fin = client.post(f"/api/v1/interviews/{iv_id}/finish", headers=H)
check("交卷生成报告", fin.status_code == 200 and fin.json()["data"]["report_id"], str(fin.status_code))

rep = client.get(f"/api/v1/interviews/{iv_id}/report", headers=H)
check("报告可获取", rep.status_code == 200, str(rep.status_code) + rep.text[:120])
data = rep.json()["data"]
ta = data.get("time_analysis")
check("报告含 time_analysis", ta is not None)
if ta:
    check("逐题用时与限时齐全",
          all("duration_sec" in i and "time_limit_sec" in i for i in ta["items"]))
    check("超时计数=1（仅被强制超时的那题）", ta["overtime_count"] == 1,
          f"ot={ta['overtime_count']} total={ta['total_answered']} rate={ta['overtime_rate']}")
    check("作答总数与逐题分析一致", ta["total_answered"] == len(data["questions_analysis"]),
          f"{ta['total_answered']} vs {len(data['questions_analysis'])}")
    check("超时技能被记录", bool(ta["overtime_skills"]), str(ta["overtime_skills"]))
    check("平均用时统计合理", ta["avg_time_sec"] >= 0 and ta["max_time_sec"] >= ta["min_time_sec"])
qa = data["questions_analysis"]
check("逐题分析含超时字段", all("overtime" in q and "duration_sec" in q for q in qa))

# ===== 8. 整场不限制提交时间（D6）：久未作答仍可继续 =====
iv5_id, _ = create_interview(1)
client.post(f"/api/v1/interviews/{iv5_id}/start", headers=H)
db = SessionLocal()
iv5 = db.query(Interview).filter(Interview.id == iv5_id).first()
iv5.started_at = datetime.utcnow() - timedelta(hours=5)
db.commit(); db.close()
d5 = answer(iv5_id, GOOD, duration_sec=5).json()["data"]
check("整场远超预计时长仍可作答", d5["total_score"] > 0, str(d5.get("total_score")))
detail = client.get(f"/api/v1/interviews/{iv5_id}", headers=H).json()["data"]
check("详情下发服务端已用时长（正计时）",
      isinstance(detail.get("elapsed_seconds"), int) and detail["elapsed_seconds"] >= 5 * 3600 - 60,
      str(detail.get("elapsed_seconds")))

print("\n" + "=" * 60)
print(f"RESULT: {len(PASS)} passed, {len(FAIL)} failed")
if FAIL:
    print("FAILED:", FAIL)
    sys.exit(1)
print("ALL CHECKS PASSED")
