from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.core.database import Base

class Interview(Base):
    __tablename__ = "interviews"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=True)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=True)
    resume_id = Column(Integer, ForeignKey("resumes.id"), nullable=True)
    jd_text = Column(Text, nullable=True)  # 本次面试使用的岗位 JD 文本快照
    type = Column(String(50), default="PERSONAL_TRAINING", nullable=False) # PERSONAL_TRAINING, ENTERPRISE_RECRUITMENT
    mode = Column(String(50), default="COMPREHENSIVE", nullable=False)     # COMPREHENSIVE, TECHNICAL, PROJECT_DEEP_DIVE, BEHAVIORAL, STRESS
    difficulty = Column(String(50), default="MEDIUM", nullable=False)      # EASY, MEDIUM, HARD
    # NORMAL 常规面试 / RETRAIN 薄弱题重练：成长曲线默认排除重练记录，避免污染趋势
    purpose = Column(String(30), default="NORMAL", nullable=False)
    derived_from_id = Column(Integer, nullable=True)  # 重练来源面试 ID（可空）
    status = Column(String(50), default="CREATED", nullable=False)         # CREATED, READY, IN_PROGRESS, PAUSED, COMPLETED, CANCELLED, EXPIRED
    current_question_seq = Column(Integer, default=1, nullable=False)
    # 当前题呈现时间：服务端据此计算单题真实用时与超时判定（不信任客户端上报）
    current_question_shown_at = Column(DateTime, nullable=True)
    paused_at = Column(DateTime, nullable=True)  # 暂停时刻：恢复时把暂停时长从呈现时间中剔除
    total_questions = Column(Integer, default=5, nullable=False)
    privacy_scope = Column(String(50), default="PRIVATE", nullable=False)  # PRIVATE, COMPANY_AUTHORIZED
    duration_minutes = Column(Integer, default=30, nullable=False)
    started_at = Column(DateTime, nullable=True)
    ended_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="interviews")
    job = relationship("Job")
    application = relationship("Application", back_populates="interviews")
    plan = relationship("InterviewPlan", back_populates="interview", uselist=False, cascade="all, delete-orphan")
    questions = relationship("InterviewQuestion", back_populates="interview", cascade="all, delete-orphan")
    report = relationship("InterviewReport", back_populates="interview", uselist=False, cascade="all, delete-orphan")
    recruiter_evaluation = relationship("RecruiterEvaluation", back_populates="interview", uselist=False, cascade="all, delete-orphan")

class InterviewPlan(Base):
    __tablename__ = "interview_plans"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    interview_id = Column(Integer, ForeignKey("interviews.id"), unique=True, nullable=False)
    stages_json = Column(Text, nullable=False)
    total_questions = Column(Integer, default=5, nullable=False)
    duration_minutes = Column(Integer, default=30, nullable=False)
    # 组卷快照：题型配比、抽题来源、题库缺口与 AI 补足情况，保证卷面可追溯可复现
    paper_json = Column(Text, nullable=True)

    interview = relationship("Interview", back_populates="plan")

class InterviewQuestion(Base):
    __tablename__ = "interview_questions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    interview_id = Column(Integer, ForeignKey("interviews.id"), nullable=False)
    parent_question_id = Column(Integer, nullable=True)
    bank_id = Column(Integer, nullable=True)  # 来源题库题目 ID（AI 动态生成的题为空）
    seq = Column(Integer, nullable=False)
    stage = Column(String(50), default="专业基础", nullable=False)
    # PROFESSIONAL 专业题 / GENERAL 通用题 / STRESS 压力题
    question_type = Column(String(20), default="PROFESSIONAL", nullable=False)
    skill_id = Column(Integer, nullable=True)
    skill_name = Column(String(100), default="Java", nullable=False)
    text = Column(Text, nullable=False)
    difficulty = Column(String(50), default="MEDIUM", nullable=False)
    # 参考答案要点（JSON 数组），逐题复盘时与候选人作答对照
    reference_points_json = Column(Text, nullable=True)
    hints = Column(String(255), nullable=True)  # 临场答题提示
    time_limit_sec = Column(Integer, default=180, nullable=False)  # 逐题建议限时
    source = Column(String(50), default="QUESTION_BANK", nullable=False)  # QUESTION_BANK, AI_GENERATED
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    interview = relationship("Interview", back_populates="questions")
    answer = relationship("InterviewAnswer", back_populates="question", uselist=False, cascade="all, delete-orphan")

class InterviewAnswer(Base):
    __tablename__ = "interview_answers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    question_id = Column(Integer, ForeignKey("interview_questions.id"), unique=True, nullable=False)
    interview_id = Column(Integer, ForeignKey("interviews.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    text = Column(Text, nullable=False)
    audio_file_id = Column(String(100), nullable=True)  # 预留：语音链路未接入，恒为 NULL
    duration_sec = Column(Integer, default=45, nullable=False)
    # 单题超时标记与超时秒数：服务端按 current_question_shown_at 判定，轻扣分不归零
    overtime = Column(Boolean, default=False, nullable=False)
    overtime_sec = Column(Integer, default=0, nullable=False)
    # 0 = 未测量。语音分析（语速/语气词）未接入前不写入假指标，历史假数据已由迁移清洗
    speaking_rate = Column(Integer, default=0, nullable=False)  # words per min
    filler_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    question = relationship("InterviewQuestion", back_populates="answer")
    evaluation = relationship("AnswerEvaluation", back_populates="answer", uselist=False, cascade="all, delete-orphan")

class AnswerEvaluation(Base):
    __tablename__ = "answer_evaluations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    answer_id = Column(Integer, ForeignKey("interview_answers.id"), unique=True, nullable=False)
    interview_id = Column(Integer, nullable=False)
    total_score = Column(Float, nullable=False)
    # Rubric: 准确度(30%), 相关性(20%), 完整性(15%), 逻辑结构(15%), 实践深度(15%), 表达能力(5%)
    dimensions_json = Column(Text, nullable=False)
    evidence_json = Column(Text, nullable=False)
    weaknesses_json = Column(Text, nullable=False)
    missing_knowledge_json = Column(Text, nullable=False)
    suggestions_json = Column(Text, nullable=False)
    next_action = Column(String(50), default="NEXT", nullable=False) # FOLLOW_UP, DEEP, BASIC, CHANGE_TOPIC, FINISH
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    answer = relationship("InterviewAnswer", back_populates="evaluation")

class InterviewReport(Base):
    __tablename__ = "interview_reports"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    interview_id = Column(Integer, ForeignKey("interviews.id"), unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    total_score = Column(Float, default=82.0, nullable=False)
    performance_level = Column(String(50), default="表现良好", nullable=False)
    # 5 radar dimensions: 专业基础, 项目经验, 系统设计, 沟通表达, 综合素质
    dimension_scores_json = Column(Text, nullable=False)
    strengths_json = Column(Text, nullable=False)
    weaknesses_json = Column(Text, nullable=False)
    suggestions_json = Column(Text, nullable=False)
    summary = Column(Text, nullable=False)
    status = Column(String(50), default="COMPLETED", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    interview = relationship("Interview", back_populates="report")

class InterviewInvitation(Base):
    __tablename__ = "interview_invitations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=False)
    interview_id = Column(Integer, nullable=True)
    note = Column(String(255), nullable=True)
    expires_at = Column(DateTime, nullable=False)
    status = Column(String(50), default="PENDING", nullable=False)  # PENDING, ACCEPTED, DECLINED, EXPIRED
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class RecruiterEvaluation(Base):
    __tablename__ = "recruiter_evaluations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=False)
    interview_id = Column(Integer, ForeignKey("interviews.id"), nullable=True)
    evaluator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    evaluator_name = Column(String(100), default="主面试官", nullable=False)
    # technical, project, problem_solving, communication, job_fit, total_score
    dimensions_json = Column(Text, nullable=False)
    summary = Column(Text, nullable=False)
    recommendation = Column(String(50), default="PASS", nullable=False) # PASS, REVIEW, REJECT
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    interview = relationship("Interview", back_populates="recruiter_evaluation")
