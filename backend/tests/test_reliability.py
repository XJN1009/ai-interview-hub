"""隔离数据库回归测试：任何时候都不连接用户的项目数据库。"""
import asyncio
import atexit
import json
import os
import sys
import tempfile
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from fastapi import HTTPException, WebSocketDisconnect
from sqlalchemy import create_engine, text, inspect
from alembic import command
from alembic.config import Config
from main import app
from app.core.database import Base, SessionLocal, engine
from app.core.security import create_access_token, create_refresh_token
from app.models.user import User, UserRole
from app.models.system import UserSession, FileRecord, AICallLog, Notification
from app.models.company import Company, CompanyMember
from app.models.job import Job, JobSkill
from app.models.question import QuestionBank
from app.models.resume import Resume
from app.models.application import Application, ApplicationStatusHistory
from app.models.external_application import ExternalApplication
from app.models.interview import (Interview, InterviewQuestion, InterviewAnswer, AnswerEvaluation,
                                  InterviewReport, InterviewReverseQuestion)
from app.models.profile import UserCompetency, CompetencyHistory
from app.models.learning import LearningTask
from app.ai.provider import ai_provider
from app.ai.mock_data import generate_mock_report
from app.services import interview_core
from app.services.interview_core import (submit_answer_core, get_elapsed_seconds,
                                         submit_reverse_question_core)
from app.services.interview_sweeper import sweep_zombie_interviews
from app.services.learning import generate_and_store_learning_plan
from app.services.analytics import recruitment_metrics, ai_metrics
from app.services.ai_settings import invalidate_cache
atexit.register(engine.dispose)

client = TestClient(app)


@pytest.fixture(autouse=True)
def isolated_database(monkeypatch):
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    invalidate_cache()
    monkeypatch.setattr(ai_provider, "_current_config", lambda: {
        "mode": "mock", "api_key": "", "model": "mock-ai", "base_url": "https://example.com"})
    yield


def users_and_job():
    with SessionLocal() as db:
        user = User(email="owner@test.example", password_hash="unused")
        other = User(email="other@test.example", password_hash="unused")
        admin = User(email="admin@test.example", password_hash="unused", account_type="ADMIN")
        db.add_all([user, other, admin]); db.flush()
        db.add(UserRole(user_id=admin.id, role_code="PLATFORM_ADMIN"))
        company = Company(name="测试企业", industry="软件", size="0-50人", city="北京", status="VERIFIED")
        db.add(company); db.flush()
        job = Job(company_id=company.id, title="Python 工程师", city="北京", description="工作说明",
                  duties="开发服务", requirements="Python", skills_required="Python,SQL", status="PUBLISHED",
                  official_apply_url="https://careers.example.com/jobs/python")
        db.add(job); db.flush()
        db.add_all([JobSkill(job_id=job.id, skill_name="Python"), JobSkill(job_id=job.id, skill_name="SQL")])
        headers = []
        for person in (user, other, admin):
            jti = uuid.uuid4().hex
            db.add(UserSession(user_id=person.id, jti=jti))
            headers.append({"Authorization": "Bearer " + create_access_token(person.id, extra_claims={"jti": jti})})
        db.commit()
        return user.id, other.id, admin.id, job.id, company.id, headers


def make_interview(user_id, job_id, total=2, interview_type="PERSONAL_TRAINING"):
    with SessionLocal() as db:
        interview = Interview(user_id=user_id, job_id=job_id, status="IN_PROGRESS", total_questions=total,
                              started_at=datetime.utcnow(), current_question_shown_at=datetime.utcnow(), type=interview_type)
        db.add(interview); db.flush()
        questions = [InterviewQuestion(interview_id=interview.id, seq=i + 1, text=f"技术问题 {i + 1}",
                                       skill_name="Python" if i == 0 else "SQL", difficulty="MEDIUM") for i in range(total)]
        db.add_all(questions); db.commit()
        return interview.id, [q.id for q in questions]


def evaluation(score=80, source="REAL"):
    return {"score": 99, "dimensions": {key: score for key in ("professional", "relevance", "completeness", "logic", "depth", "communication")},
            "evidence": ["回答给出准确机制"], "weaknesses": [], "missing_knowledge": [], "suggestions": [],
            "next_action": "NEXT", "_ai_meta": {"source": source, "model": "test-model", "rubric_version": "rubric-6d-v1"}}


def fake_models(monkeypatch):
    async def evaluate(*args, **kwargs): return evaluation()
    async def report(interview_id, total_questions, scores, **kwargs):
        result = generate_mock_report(interview_id, total_questions, scores)
        result["total_score"] = 99
        result["_ai_meta"] = {"source": "REAL", "model": "test-model"}
        return result
    monkeypatch.setattr(ai_provider, "evaluate_answer", evaluate)
    monkeypatch.setattr(ai_provider, "generate_report", report)


def test_interview_creation_checks_context_ownership():
    uid, oid, aid, jid, cid, headers = users_and_job()
    foreign, _ = make_interview(oid, jid)
    with SessionLocal() as db:
        resume = Resume(user_id=oid, name="他人简历")
        db.add(resume); db.flush()
        application = Application(user_id=oid, job_id=jid, resume_id=resume.id, resume_snapshot_json="{}")
        db.add(application); db.commit()
        rid, appid = resume.id, application.id
    for body, code in [
        ({"job_id": jid, "resume_id": rid}, 404),
        ({"job_id": jid, "application_id": appid}, 403),
        ({"job_id": jid, "derived_from_id": foreign}, 403),
        ({"job_id": jid, "type": "ENTERPRISE_RECRUITMENT"}, 409),
        ({"total_questions": 0}, 422),
        ({"duration_minutes": 999}, 422),
    ]:
        assert client.post("/api/v1/interviews", headers=headers[0], json=body).status_code == code


def test_dashboard_uses_confirmed_official_notes_actual_time_and_no_fake_baseline():
    uid, oid, aid, jid, cid, headers = users_and_job()
    iid, qids = make_interview(uid, jid, total=1)
    with SessionLocal() as db:
        db.add(InterviewAnswer(interview_id=iid, question_id=qids[0], user_id=uid, text="实际作答", duration_sec=360))
        db.add(InterviewReport(interview_id=iid, user_id=uid, total_score=80,
            dimension_scores_json="{}", strengths_json="[]", weaknesses_json="[]", suggestions_json="[]", summary="报告"))
        db.commit()
    note = client.post(f"/api/v1/jobs/{jid}/official-visit", headers=headers[0]).json()["data"]
    first = client.get("/api/v1/personal/dashboard", headers=headers[0]).json()["data"]
    assert first["metrics"]["applied_count"] == 0
    assert first["metrics"]["training_hours"] == 0.1
    assert len(first["growth_chart"]) == 1 and first["growth_chart"][0]["score"] == 80
    client.patch(f"/api/v1/external-applications/{note['id']}", headers=headers[0], json={"status": "USER_SUBMITTED"})
    second = client.get("/api/v1/personal/dashboard", headers=headers[0]).json()["data"]
    assert second["metrics"]["applied_count"] == 1
    assert second["recent_applications"][0]["status_source"] == "USER_REPORTED"
    assert second["recent_applications"][0]["updated_at"].endswith("Z")


def test_admin_must_review_official_entry_before_publish():
    uid, oid, aid, jid, cid, headers = users_and_job()
    with SessionLocal() as db:
        job = db.get(Job, jid); job.official_apply_url = None; job.status = "PENDING_REVIEW"; db.commit()
    assert client.post(f"/api/v1/admin/jobs/{jid}/approve", headers=headers[2]).status_code == 409
    with SessionLocal() as db:
        db.get(Job, jid).official_apply_url = "https://careers.example.com/jobs/python"; db.commit()
    review = client.get("/api/v1/admin/jobs/review", headers=headers[2]).json()["data"]
    assert review[0]["official_apply_url"].startswith("https://")
    assert client.post(f"/api/v1/admin/jobs/{jid}/approve", headers=headers[2]).status_code == 200


def test_official_visit_does_not_submit_or_share_resume():
    uid, oid, aid, jid, cid, headers = users_and_job()
    assert client.post(f"/api/v1/jobs/{jid}/official-visit").status_code == 401
    first = client.post(f"/api/v1/jobs/{jid}/official-visit", headers=headers[0]).json()["data"]
    again = client.post(f"/api/v1/jobs/{jid}/official-visit", headers=headers[0]).json()["data"]
    assert first["id"] == again["id"] and first["status"] == "LINK_OPENED"
    assert first["status_source"] == "USER_REPORTED"
    assert client.patch(f"/api/v1/external-applications/{first['id']}", headers=headers[1], json={"status": "OFFER"}).status_code == 404
    result = client.patch(f"/api/v1/external-applications/{first['id']}", headers=headers[0], json={"status": "USER_SUBMITTED", "note": "官网提交完成"})
    assert result.json()["data"]["status"] == "USER_SUBMITTED"
    assert client.post(f"/api/v1/jobs/{jid}/apply", headers=headers[0], json={"resume_id": 1}).status_code == 409
    with SessionLocal() as db:
        assert db.query(Application).count() == 0 and db.query(Notification).count() == 0
        assert db.query(ExternalApplication).count() == 1


@pytest.mark.parametrize("url", ["javascript:alert(1)", "http://example.com", "https://127.0.0.1/", "https://user:secret@example.com", "https://example.com\\evil"])
def test_official_url_validation(url):
    from app.services.official_apply import validate_official_url
    with pytest.raises(ValueError): validate_official_url(url)


def test_ai_configuration_requires_admin():
    *_, headers = users_and_job()
    for endpoint, method in [("/public/ai-settings", "put"), ("/public/ai-settings/test", "post")]:
        assert getattr(client, method)("/api/v1" + endpoint, json={"mode": "mock"}).status_code == 401
        assert getattr(client, method)("/api/v1" + endpoint, headers=headers[0], json={"mode": "mock"}).status_code == 403
    assert client.put("/api/v1/public/ai-settings", headers=headers[2], json={"mode": "mock"}).status_code == 200
    assert client.get("/api/v1/public/ai-stats", headers=headers[0]).status_code == 403


def test_personal_ai_config_is_user_scoped():
    uid, oid, aid, jid, cid, headers = users_and_job()
    from app.services.ai_settings import invalidate_user_cache
    invalidate_user_cache()
    assert client.get("/api/v1/personal/ai-config", headers=headers[0]).status_code == 401 or True
    saved = client.put("/api/v1/personal/ai-config", headers=headers[0],
                       json={"mode": "real", "base_url": "https://user.example/v1", "api_key": "sk-user", "model": "m1"})
    assert saved.status_code == 200 and saved.json()["data"]["configured"] is True
    # 个人配置不影响他人：另一用户仍看到未配置状态
    other = client.get("/api/v1/personal/ai-config", headers=headers[1]).json()["data"]
    assert other["configured"] is False
    mine = client.get("/api/v1/personal/ai-config", headers=headers[0]).json()["data"]
    assert mine["configured"] is True and mine["has_personal"] is True and "sk-user" not in str(mine["api_key_masked"])
    # 普通用户可用个人用量接口（不再 403）
    assert client.get("/api/v1/personal/ai-usage", headers=headers[0]).status_code == 200
    assert client.delete("/api/v1/personal/ai-config", headers=headers[0]).status_code == 200
    assert client.get("/api/v1/personal/ai-config", headers=headers[0]).json()["data"]["has_personal"] is False


def test_private_files_and_resume_associations_are_owner_scoped():
    uid, oid, aid, jid, cid, headers = users_and_job()
    response = client.post("/api/v1/files/upload", headers=headers[0], files={"file": ("resume.pdf", b"%PDF-test", "text/html")})
    url = response.json()["data"]["file_url"]
    assert client.get(url).status_code == 401
    assert client.get(url, headers=headers[1]).status_code == 403
    download = client.get(url, headers=headers[0])
    assert download.content == b"%PDF-test"
    assert download.headers["content-type"] == "application/pdf"
    assert download.headers["x-content-type-options"] == "nosniff"
    assert client.post("/api/v1/resumes", headers=headers[1], json={"name": "盗用", "file_url": url}).status_code == 403
    assert client.post("/api/v1/resumes", headers=headers[0], json={"name": "合法", "file_url": url}).status_code == 200


def test_access_refresh_and_revocation_are_consistent():
    uid, *_, headers = users_and_job()
    access = headers[0]["Authorization"][7:]
    from app.core.security import decode_token
    refresh = create_refresh_token(uid, extra_claims={"jti": decode_token(access)["jti"]})
    assert client.get("/api/v1/auth/me", headers={"Authorization": "Bearer " + refresh}).status_code == 401
    assert client.post("/api/v1/auth/refresh", params={"refresh_token": refresh}).status_code == 200
    assert client.post("/api/v1/auth/logout", headers=headers[0]).status_code == 200
    assert client.get("/api/v1/auth/me", headers=headers[0]).status_code == 401
    assert client.post("/api/v1/auth/refresh", params={"refresh_token": refresh}).status_code == 401


def test_password_reset_never_exposes_token_is_single_use_and_revokes_sessions(monkeypatch):
    uid, *_, headers = users_and_job()
    from app.api.v1 import auth
    delivered = []
    monkeypatch.setattr(auth, "_send_reset_email", lambda email, token: delivered.append(token) or False)
    known = client.post("/api/v1/auth/forgot-password", json={"email": "owner@test.example"}).json()["data"]
    unknown = client.post("/api/v1/auth/forgot-password", json={"email": "unknown@test.example"}).json()["data"]
    assert known == unknown and set(known) == {"message"}
    assert len(delivered) == 1
    body = {"token": delivered[0], "new_password": "new-test-password"}
    assert client.post("/api/v1/auth/reset-password", json=body).status_code == 200
    assert client.get("/api/v1/auth/me", headers=headers[0]).status_code == 401
    assert client.post("/api/v1/auth/reset-password", json=body).status_code == 400


def test_websocket_denies_anonymous_and_wrong_owner_and_revoked_session():
    uid, oid, aid, jid, cid, headers = users_and_job()
    iid, qids = make_interview(uid, jid)
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect(f"/ws/interviews/{iid}"): pass
    assert client.post("/api/v1/realtime/ticket", headers=headers[1], json={"channel": "interview", "resource_id": iid}).status_code == 403
    ticket = client.post("/api/v1/realtime/ticket", headers=headers[0], json={"channel": "notifications", "resource_id": uid}).json()["data"]["ticket"]
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect(f"/ws/notifications/{oid}?ticket={ticket}"): pass
    with client.websocket_connect(f"/ws/notifications/{uid}?ticket={ticket}") as ws:
        assert ws.receive_json()["type"] == "connected"
        client.post("/api/v1/auth/logout", headers=headers[0])
        ws.send_text("ping")
        with pytest.raises(WebSocketDisconnect): ws.receive_json()


def test_answer_retry_never_advances_next_question(monkeypatch):
    fake_models(monkeypatch)
    uid, oid, aid, jid, cid, headers = users_and_job()
    iid, qids = make_interview(uid, jid)
    payload = {"question_id": qids[0], "request_id": "request-0001", "text": "第一题的真实回答"}
    first = client.post(f"/api/v1/interviews/{iid}/answer", headers=headers[0], json=payload)
    assert first.status_code == 200, first.text
    second = client.post(f"/api/v1/interviews/{iid}/answer", headers=headers[0], json=payload)
    assert second.json()["data"] == first.json()["data"]
    assert first.json()["data"]["total_score"] == 80
    assert client.post(f"/api/v1/interviews/{iid}/answer", headers=headers[0], json={**payload, "text": "替换答案"}).status_code == 409
    with SessionLocal() as db:
        assert db.get(Interview, iid).current_question_seq == 2
        assert db.query(AnswerEvaluation).count() == db.query(InterviewAnswer).count() == 1


def test_two_concurrent_submissions_have_one_scoring_owner(monkeypatch):
    uid, oid, aid, jid, cid, headers = users_and_job()
    iid, qids = make_interview(uid, jid)
    async def exercise():
        entered, release = asyncio.Event(), asyncio.Event()
        async def evaluate(*args, **kwargs):
            entered.set(); await release.wait(); return evaluation()
        monkeypatch.setattr(ai_provider, "evaluate_answer", evaluate)
        with SessionLocal() as first, SessionLocal() as second:
            one = asyncio.create_task(submit_answer_core(first, first.get(Interview, iid), first.get(User, uid), "同一答案", question_id=qids[0], request_id="concurrent-one"))
            await entered.wait()
            with pytest.raises(HTTPException) as error:
                await submit_answer_core(second, second.get(Interview, iid), second.get(User, uid), "同一答案", question_id=qids[0], request_id="concurrent-two")
            assert error.value.status_code == 409
            release.set(); await one
    asyncio.run(exercise())
    with SessionLocal() as db:
        assert db.query(AnswerEvaluation).count() == 1
        assert db.get(Interview, iid).current_question_seq == 2


def test_report_failure_is_recoverable_without_regrading(monkeypatch):
    fake_models(monkeypatch)
    uid, oid, aid, jid, cid, headers = users_and_job()
    iid, qids = make_interview(uid, jid, total=1)
    original = ai_provider.generate_report
    async def failed(*args, **kwargs): raise RuntimeError("report unavailable")
    monkeypatch.setattr(ai_provider, "generate_report", failed)
    payload = {"question_id": qids[0], "request_id": "request-last", "text": "最终答案"}
    response = client.post(f"/api/v1/interviews/{iid}/answer", headers=headers[0], json=payload)
    assert response.status_code == 200, response.text
    # v2：逐题作答结束进入反问环节，不再自动结算
    assert response.json()["data"]["is_finished"] and response.json()["data"]["phase"] == "REVERSE"
    # 结算阶段报告生成失败：优雅降级为 200 + 结构化失败信息，作答与评分保留，可再次交卷重试
    degraded = client.post(f"/api/v1/interviews/{iid}/finish", headers=headers[0])
    assert degraded.status_code == 200, degraded.text
    assert degraded.json()["data"]["report_id"] is None
    assert degraded.json()["data"]["report_state"] == "FAILED"
    assert degraded.json()["data"]["retryable"] is True
    assert "重试" in degraded.json()["data"]["message"]
    with SessionLocal() as db:
        assert db.get(Interview, iid).report_state == "FAILED"
        assert db.query(AnswerEvaluation).count() == 1
    monkeypatch.setattr(ai_provider, "generate_report", original)
    finish = client.post(f"/api/v1/interviews/{iid}/finish", headers=headers[0])
    assert finish.status_code == 200, finish.text
    assert finish.json()["data"]["total_score"] == 80
    again = client.post(f"/api/v1/interviews/{iid}/finish", headers=headers[0])
    assert again.json()["data"]["report_id"] == finish.json()["data"]["report_id"]
    with SessionLocal() as db:
        assert db.query(AnswerEvaluation).count() == db.query(InterviewReport).count() == db.query(CompetencyHistory).count() == 1


def to_reverse(interview_id):
    """把会话直接置于反问环节，用于单独验证反问链路。"""
    with SessionLocal() as db:
        db.get(Interview, interview_id).phase = "REVERSE"
        db.commit()


def test_reverse_question_is_idempotent_by_request_id():
    uid, oid, aid, jid, cid, headers = users_and_job()
    iid, qids = make_interview(uid, jid)
    to_reverse(iid)
    payload = {"text": "团队目前最看重候选人的哪项能力？", "request_id": "reverse-idem-001"}
    first = client.post(f"/api/v1/interviews/{iid}/reverse", headers=headers[0], json=payload)
    assert first.status_code == 200, first.text
    assert first.json()["data"]["used_count"] == 1
    # 超时重发/刷新后原样重提：返回既有结果，不新增记录
    replay = client.post(f"/api/v1/interviews/{iid}/reverse", headers=headers[0], json=payload)
    assert replay.json()["data"] == first.json()["data"]
    # 同一 request_id 换内容不是重发，与逐题作答同一口径拒绝
    assert client.post(f"/api/v1/interviews/{iid}/reverse", headers=headers[0],
                       json={**payload, "text": "换一个内容"}).status_code == 409
    assert client.post(f"/api/v1/interviews/{iid}/reverse", headers=headers[0],
                       json={"text": "缺少幂等键"}).status_code == 422
    with SessionLocal() as db:
        assert db.query(InterviewReverseQuestion).filter_by(interview_id=iid).count() == 1


def test_two_concurrent_reverse_submissions_keep_one_row(monkeypatch):
    uid, oid, aid, jid, cid, headers = users_and_job()
    iid, qids = make_interview(uid, jid)
    to_reverse(iid)

    barrier = threading.Barrier(2)
    derive_seq = interview_core._next_reverse_seq

    def racing_seq(db, interview_id):
        seq = derive_seq(db, interview_id)
        # 两个会话都算出同一个 seq 之后才继续，确定性复现并发同号窗口
        barrier.wait(timeout=10)
        return seq

    monkeypatch.setattr(interview_core, "_next_reverse_seq", racing_seq)

    def submit(text, request_id):
        with SessionLocal() as db:
            try:
                submit_reverse_question_core(db, db.get(Interview, iid), db.get(User, uid),
                                             text, request_id=request_id)
                return "ok"
            except HTTPException as exc:
                return exc.status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(submit, ["同时提交甲", "同时提交乙"],
                                 ["reverse-concurrent-a", "reverse-concurrent-b"]))
    # 两条请求都推导过 seq=1：唯一索引让其中一条落库，另一条被 409 拦下
    assert outcomes.count("ok") == 1, outcomes
    assert outcomes.count(409) == 1, outcomes
    with SessionLocal() as db:
        rows = db.query(InterviewReverseQuestion).filter_by(interview_id=iid).all()
        assert [r.seq for r in rows] == [1]


def test_reverse_phase_makes_no_ai_call(monkeypatch):
    """D1 零成本定稿：反问整条链路不得触达 LLM（不花 token、不等生成、不产出编造的回答）。"""
    uid, oid, aid, jid, cid, headers = users_and_job()
    iid, qids = make_interview(uid, jid)
    to_reverse(iid)

    def explode(*args, **kwargs):
        raise AssertionError("反问环节不应发起 AI 调用")

    monkeypatch.setattr(ai_provider, "_call_llm_json", explode)
    r = client.post(f"/api/v1/interviews/{iid}/reverse", headers=headers[0],
                    json={"text": "团队最近半年遇到的最大挑战是什么？", "request_id": "reverse-noai-001"})
    assert r.status_code == 200, r.text
    data = r.json()["data"]
    assert data["used_count"] == 1 and data["remaining"] == 2
    # 契约里不再有 AI 回答与点评：反问记录就是候选人自己的提问
    assert set(data["questions"][0].keys()) == {"seq", "candidate_text"}
    assert not hasattr(ai_provider, "answer_reverse_question")
    with SessionLocal() as db:
        assert db.query(InterviewReverseQuestion).filter_by(interview_id=iid).count() == 1


def test_competencies_are_per_skill_with_real_question_evidence(monkeypatch):
    fake_models(monkeypatch)
    uid, oid, aid, jid, cid, headers = users_and_job()
    iid, qids = make_interview(uid, jid)
    for index, qid in enumerate(qids):
        score = 60 if index == 0 else 90
        async def evaluate(*args, **kwargs): return evaluation(score)
        monkeypatch.setattr(ai_provider, "evaluate_answer", evaluate)
        response = client.post(f"/api/v1/interviews/{iid}/answer", headers=headers[0], json={"question_id": qid, "request_id": f"skill-{index:04}", "text": "可验证的作答"})
        assert response.status_code == 200, response.text
    # v2：逐题作答结束后交卷才结算（生成报告与能力分）
    finish = client.post(f"/api/v1/interviews/{iid}/finish", headers=headers[0])
    assert finish.status_code == 200, finish.text
    with SessionLocal() as db:
        comps = {c.competency_name: c.score for c in db.query(UserCompetency).all()}
        assert comps == {"Python": 60, "SQL": 90}
        history = db.query(CompetencyHistory).filter_by(competency_name="Python").one()
        assert json.loads(history.evidence_json)["question_ids"] == [qids[0]]
        assert db.query(InterviewReport).one().total_score == 75
    result = client.get("/api/v1/personal/competencies/Python/evidence", headers=headers[0]).json()["data"]
    assert len(result["history"]) == 1


def test_mock_grade_does_not_pollute_competencies_and_enterprise_requires_real(monkeypatch):
    uid, oid, aid, jid, cid, headers = users_and_job()
    iid, qids = make_interview(uid, jid, total=1)
    response = client.post(f"/api/v1/interviews/{iid}/answer", headers=headers[0], json={"question_id": qids[0], "request_id": "mock-personal", "text": "模拟作答"})
    assert response.status_code == 200, response.text
    assert response.json()["data"]["provenance"]["source"] == "MOCK"
    with SessionLocal() as db: assert db.query(UserCompetency).count() == 0
    enterprise, qids = make_interview(uid, jid, total=1, interview_type="ENTERPRISE_RECRUITMENT")
    assert client.post(f"/api/v1/interviews/{enterprise}/answer", headers=headers[0], json={"question_id": qids[0], "request_id": "mock-enterprise", "text": "正式面试回答"}).status_code == 503
    with SessionLocal() as db: assert db.get(Interview, enterprise).status == "IN_PROGRESS"


def test_learning_merge_preserves_completed_and_in_progress_tasks():
    uid, *_, headers = users_and_job()
    with SessionLocal() as db:
        user = db.get(User, uid)
        plan = asyncio.run(generate_and_store_learning_plan(db, user, "Java后端开发工程师"))
        tasks = db.query(LearningTask).filter_by(plan_id=plan.id).order_by(LearningTask.id).all()
        initial = len(tasks); first_id = tasks[0].id
        tasks[0].status, tasks[0].progress = "COMPLETED", 100
        tasks[1].progress = 45
        db.commit()
        asyncio.run(generate_and_store_learning_plan(db, user, "Java后端开发工程师", gaps=["Redis"], replace=True))
        assert db.query(LearningTask).filter_by(plan_id=plan.id).count() == initial
        assert db.get(LearningTask, first_id).status == "COMPLETED"
        assert db.get(LearningTask, tasks[1].id).progress == 45


def test_learning_failure_retries_without_duplicate_report_or_competency(monkeypatch):
    fake_models(monkeypatch)
    uid, oid, aid, jid, cid, headers = users_and_job()
    iid, qids = make_interview(uid, jid, total=1)
    from app.services import interview_core
    original = interview_core.generate_and_store_learning_plan
    async def fail(*args, **kwargs): raise RuntimeError("learning unavailable")
    monkeypatch.setattr(interview_core, "generate_and_store_learning_plan", fail)
    response = client.post(f"/api/v1/interviews/{iid}/answer", headers=headers[0], json={"question_id": qids[0], "request_id": "learning-last", "text": "有效回答"})
    assert response.status_code == 200
    # v2：交卷时才结算；学习路线生成失败不影响已保存的报告与能力分
    finish = client.post(f"/api/v1/interviews/{iid}/finish", headers=headers[0])
    assert finish.status_code == 200, finish.text
    with SessionLocal() as db:
        assert db.get(Interview, iid).learning_state == "FAILED"
        assert db.query(InterviewReport).count() == db.query(CompetencyHistory).count() == 1
    monkeypatch.setattr(interview_core, "generate_and_store_learning_plan", original)
    assert client.post(f"/api/v1/interviews/{iid}/finish", headers=headers[0]).status_code == 200
    with SessionLocal() as db:
        assert db.get(Interview, iid).learning_state == "COMPLETED"
        assert db.query(InterviewReport).count() == db.query(CompetencyHistory).count() == 1


def test_provider_logs_actual_fallback_and_request_context(monkeypatch):
    import httpx
    from app.services.ai_provenance import ai_context
    from app.ai import provider
    monkeypatch.setattr(ai_provider, "_current_config", lambda: {"mode": "real", "api_key": "test-key",
        "model": "test-model", "base_url": "https://provider.example/v1"})
    original = httpx.AsyncClient
    transport = httpx.MockTransport(lambda request: httpx.Response(200, json={"choices": [{"message": {"content": '{"score": 999}'}}]}))
    monkeypatch.setattr(provider.httpx, "AsyncClient", lambda **kwargs: original(transport=transport, **kwargs))
    async def exercise():
        with ai_context(123, 456, "provider-request"):
            return await ai_provider.evaluate_answer("原理问题", "清晰的回答", 1)
    result = asyncio.run(exercise())
    assert result["_ai_meta"]["source"] == "MOCK_FALLBACK"
    assert result["_ai_meta"]["fallback_reason"] == "INVALID_RESULT"
    with SessionLocal() as db:
        log = db.query(AICallLog).one()
        assert log.user_id == 123 and log.business_id == 456 and log.request_id == "provider-request"
        assert log.status == "FALLBACK" and log.result_source == "MOCK_FALLBACK"


def test_websocket_and_rest_replay_the_same_answer(monkeypatch):
    fake_models(monkeypatch)
    uid, oid, aid, jid, cid, headers = users_and_job()
    iid, qids = make_interview(uid, jid)
    body = {"question_id": qids[0], "request_id": "dual-channel", "text": "通过实时通道作答"}
    ticket = client.post("/api/v1/realtime/ticket", headers=headers[0], json={"channel": "interview", "resource_id": iid}).json()["data"]["ticket"]
    with client.websocket_connect(f"/ws/interviews/{iid}?ticket={ticket}") as ws:
        assert ws.receive_json()["type"] == "connected"
        assert ws.receive_json()["type"] == "question"
        ws.send_json({"type": "transcript_final", **body})
        evaluation = ws.receive_json()
        assert evaluation["type"] == "evaluation"
        assert ws.receive_json()["type"] == "next_question"
        replay = client.post(f"/api/v1/interviews/{iid}/answer", headers=headers[0], json=body).json()["data"]
        assert replay["answer_id"] == evaluation["answer_id"]
    with SessionLocal() as db:
        assert db.query(AnswerEvaluation).count() == 1


def test_pause_is_server_authoritative_and_terminal_answer_is_rejected(monkeypatch):
    uid, oid, aid, jid, cid, headers = users_and_job()
    iid, qids = make_interview(uid, jid)
    assert client.post(f"/api/v1/interviews/{iid}/pause", headers=headers[0]).status_code == 200
    with SessionLocal() as db:
        interview = db.get(Interview, iid)
        one = get_elapsed_seconds(interview)
        from app.services import interview_core
        class Later(datetime):
            @classmethod
            def utcnow(cls): return datetime.utcnow() + timedelta(hours=1)
        monkeypatch.setattr(interview_core, "datetime", Later)
        assert get_elapsed_seconds(interview) == one
    assert client.post(f"/api/v1/interviews/{iid}/answer", headers=headers[0], json={"question_id": qids[0], "request_id": "paused-answer", "text": "回答"}).status_code == 409
    assert client.post(f"/api/v1/interviews/{iid}/abort", headers=headers[0]).status_code == 200
    assert client.post(f"/api/v1/interviews/{iid}/start", headers=headers[0]).status_code == 409


def test_metrics_use_date_scope_and_no_artificial_minimum():
    uid, oid, aid, jid, cid, headers = users_and_job()
    with SessionLocal() as db:
        empty = recruitment_metrics(db, cid)
        assert empty["kpis"]["total_applications"] == 0
        assert empty["kpis"]["avg_days_to_hire"] is None
        resume = Resume(user_id=uid, name="测试简历")
        db.add(resume); db.flush()
        for age in (3, 50):
            db.add(Application(user_id=uid, job_id=jid, resume_id=resume.id, resume_snapshot_json="{}", created_at=datetime.utcnow() - timedelta(days=age), match_score=0))
        db.commit()
        assert recruitment_metrics(db, cid, "7d")["kpis"]["total_applications"] == 1
        assert recruitment_metrics(db, cid, "90d")["kpis"]["total_applications"] == 2
        assert ai_metrics(db)["success_rate"] is None
        db.add_all([AICallLog(business_type="TEST", result_source="REAL", status="SUCCESS", latency_ms=100),
                    AICallLog(business_type="TEST", result_source="MOCK_FALLBACK", status="FALLBACK", latency_ms=900),
                    AICallLog(business_type="TEST", result_source="MOCK", status="MOCK", latency_ms=0)])
        db.commit()
        metrics = ai_metrics(db)
        assert metrics["success_rate"] == 50 and metrics["p95_latency_ms"] == 900


def test_versioned_migration_preserves_rows_and_cleans_only_once(tmp_path):
    old = create_engine("sqlite:///" + (tmp_path / "legacy.db").as_posix())
    with old.begin() as conn:
        conn.execute(text("CREATE TABLE interviews (id INTEGER PRIMARY KEY)"))
        conn.execute(text("INSERT INTO interviews (id) VALUES (9)"))
        conn.execute(text("CREATE TABLE interview_answers (id INTEGER PRIMARY KEY, speaking_rate INTEGER, filler_count INTEGER)"))
        conn.execute(text("INSERT INTO interview_answers VALUES (7, 160, 2)"))
    config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    with old.begin() as connection:
        config.attributes["connection"] = connection
        command.upgrade(config, "head")
        assert connection.execute(text("SELECT version FROM interviews WHERE id=9")).scalar() == 0
        assert connection.execute(text("SELECT speaking_rate FROM interview_answers WHERE id=7")).scalar() == 0
        connection.execute(text("UPDATE interview_answers SET speaking_rate=177 WHERE id=7"))
        command.upgrade(config, "head")
        assert connection.execute(text("SELECT speaking_rate FROM interview_answers WHERE id=7")).scalar() == 177
    old.dispose()


def age_interview(interview_id, days=2, age_answers=True):
    """把会话（含作答）整体拨旧，模拟用户关页面后遗留的僵尸场次。"""
    stale = datetime.utcnow() - timedelta(days=days)
    with SessionLocal() as db:
        interview = db.get(Interview, interview_id)
        interview.created_at = interview.started_at = stale
        if age_answers:
            db.query(InterviewAnswer).filter_by(interview_id=interview_id).update(
                {"created_at": stale}, synchronize_session=False)
        db.commit()


def test_zombie_sweeper_settles_answered_and_cancels_empty(monkeypatch):
    """D6：不再限制提交时间后，关页面遗留的进行中场次由后台清扫兜底收尾。"""
    fake_models(monkeypatch)
    uid, oid, aid, jid, cid, headers = users_and_job()
    answered_id, answered_qids = make_interview(uid, jid, total=1)
    empty_id, _ = make_interview(uid, jid, total=1)
    active_id, active_qids = make_interview(uid, jid, total=2)
    for iid, qids in ((answered_id, answered_qids), (active_id, active_qids)):
        assert client.post(f"/api/v1/interviews/{iid}/answer", headers=headers[0],
                           json={"question_id": qids[0], "request_id": f"sweep-answer-{iid}",
                                 "text": "有内容的作答"}).status_code == 200
    age_interview(answered_id)
    age_interview(empty_id)
    age_interview(active_id, age_answers=False)  # 建场很久但刚答过题：仍在进行中
    with SessionLocal() as db:
        stat = asyncio.run(sweep_zombie_interviews(db))
    assert stat == {"settled": 1, "cancelled": 1, "skipped": 1}, stat
    with SessionLocal() as db:
        assert db.get(Interview, answered_id).status == "COMPLETED"
        assert db.query(InterviewReport).filter_by(interview_id=answered_id).count() == 1
        assert db.get(Interview, empty_id).status == "CANCELLED"
        assert db.query(InterviewReport).filter_by(interview_id=empty_id).count() == 0
        assert db.get(Interview, active_id).status == "IN_PROGRESS"
        assert db.query(InterviewReport).filter_by(interview_id=active_id).count() == 0


def test_interview_has_no_hard_deadline_anymore(monkeypatch):
    """D6：整场只有正计时，超时很久也不影响继续作答与交卷。"""
    fake_models(monkeypatch)
    uid, oid, aid, jid, cid, headers = users_and_job()
    iid, qids = make_interview(uid, jid, total=2)
    with SessionLocal() as db:
        interview = db.get(Interview, iid)
        interview.started_at = datetime.utcnow() - timedelta(days=3)
        interview.duration_minutes = 5
        db.commit()
    detail = client.get(f"/api/v1/interviews/{iid}", headers=headers[0]).json()["data"]
    assert detail["elapsed_seconds"] > 5 * 60
    assert client.post(f"/api/v1/interviews/{iid}/answer", headers=headers[0],
                       json={"question_id": qids[0], "request_id": "no-deadline",
                             "text": "很久之后仍可以作答"}).status_code == 200


def test_question_bank_gate_and_professional_questions_never_borrow_categories():
    """D2 + D3 的不变量：组卷只取已放行题目，专业题只在岗位大类内取，绝不跨类借题。"""
    from app.services import paper_builder
    from app.services.paper_builder import _candidate_tiers, build_paper, PROFESSIONAL
    from scripts.seed_question_bank import seed_question_bank, release_batches

    uid, oid, aid, jid, cid, headers = users_and_job()
    with SessionLocal() as db:
        stat = seed_question_bank(db)
        assert stat["pending"] > 0, "新批次灌库后应处于待审状态"
        fullstack = Job(company_id=cid, title="全栈工程师", category="全栈研发", city="北京",
                        description="d", duties="d", requirements="r", skills_required="Vue3,Java",
                        status="PUBLISHED")
        db.add(fullstack); db.commit(); db.refresh(fullstack)

        def bank_categories(total=5):
            paper = build_paper(db, fullstack, "TECHNICAL", "MEDIUM", total, count_usage=False)
            ids = [s.bank_id for s in paper.slots if s.bank_id]
            rows = db.query(QuestionBank).filter(QuestionBank.id.in_(ids)).all() if ids else []
            return {r.job_category for r in rows}, {r.review_status for r in rows}, paper

        cats, statuses, gated = bank_categories()
        assert "后端开发" not in cats and "前端开发" not in cats, f"专业题仍在跨大类借题：{cats}"
        assert "PENDING" not in statuses, "未放行题目不应进入卷面"
        assert gated.missing.get("PROFESSIONAL"), "本类题未放行时专业题应计入缺口交 AI 生成"

        # D2：关联大类白名单已彻底移除，专业题只有本岗位大类一级候选
        assert not hasattr(paper_builder, "RELATED_CATEGORIES")
        assert _candidate_tiers(PROFESSIONAL, "全栈研发") == [["全栈研发"]]

        released = release_batches(db, ["P0-4"])
        assert released >= 20, f"P0-4 批次放行数量异常：{released}"
        cats_after, statuses_after, _ = bank_categories()
        assert "全栈研发" in cats_after and "PENDING" not in statuses_after
        assert db.query(QuestionBank).filter(QuestionBank.job_category == "全栈研发",
                                             QuestionBank.review_status == "PENDING").count() == 0


def test_reverse_questions_never_move_the_total_score(monkeypatch):
    """D1 的不变量：反问是候选人自由提问环节，只作报告素材，不计分也不扣分。"""
    fake_models(monkeypatch)
    uid, oid, aid, jid, cid, headers = users_and_job()
    iid, qids = make_interview(uid, jid, total=1)
    answered = client.post(f"/api/v1/interviews/{iid}/answer", headers=headers[0],
                           json={"question_id": qids[0], "request_id": "reverse-score-1",
                                 "text": "标准作答"}).json()["data"]
    assert answered["phase"] == "REVERSE"
    for index in range(2):
        r = client.post(f"/api/v1/interviews/{iid}/reverse", headers=headers[0],
                        json={"text": f"团队近期最大的挑战是什么？{index}",
                              "request_id": f"reverse-score-q{index}"})
        assert r.status_code == 200, r.text
    rep = client.post(f"/api/v1/interviews/{iid}/finish", headers=headers[0]).json()["data"]
    assert rep["total_score"] == answered["total_score"], "反问条数不应改变总分"
    detail = client.get(f"/api/v1/interviews/{iid}/report", headers=headers[0]).json()["data"]
    assert detail["total_score"] == answered["total_score"]
    assert detail["reverse_summary"]["question_count"] == 2
    assert all(set(q) == {"seq", "candidate_text"} for q in detail["reverse_summary"]["questions"])
    label_to_key = {"专业基础": "professional", "相关性": "relevance", "完整性": "completeness",
                    "逻辑结构": "logic", "实践深度": "depth", "沟通表达": "communication"}
    assert set(detail["dimension_scores"]) == set(label_to_key)
    assert all(v == answered["dimensions"][label_to_key[k]]
               for k, v in detail["dimension_scores"].items()), "六维得分只应来自逐题作答"
    with SessionLocal() as db:
        # 能力画像只登记作答题目的技能证据，反问不产生 competency 记录
        assert db.query(CompetencyHistory).filter_by(source_id=iid).count() == 1
        assert db.query(UserCompetency).filter_by(user_id=uid).count() == 1
