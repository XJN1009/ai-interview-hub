from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field
from datetime import datetime

class InterviewCreate(BaseModel):
    job_id: Optional[int] = None
    resume_id: Optional[int] = None
    application_id: Optional[int] = None
    type: Literal["PERSONAL_TRAINING", "ENTERPRISE_RECRUITMENT"] = "PERSONAL_TRAINING"
    mode: str = "COMPREHENSIVE"     # COMPREHENSIVE, TECHNICAL, PROJECT_DEEP_DIVE, BEHAVIORAL, STRESS
    difficulty: str = "MEDIUM"      # EASY, MEDIUM, HARD
    total_questions: int = Field(default=5, ge=1, le=30)
    duration_minutes: int = Field(default=30, ge=1, le=180)
    jd_text: Optional[str] = None   # 用户输入的/自动带出的岗位 JD 文本
    use_question_bank: bool = True  # 是否优先从结构化题库组卷（关闭则全部 AI 实时生成）
    selected_bank_ids: Optional[List[int]] = None  # 按已预览确认的考卷出题（题库题目 ID，按顺序）
    purpose: str = "NORMAL"          # NORMAL 常规 / RETRAIN 薄弱题重练
    derived_from_id: Optional[int] = None  # 重练来源面试 ID

class InterviewQuestionOut(BaseModel):
    id: int
    seq: int
    stage: str
    question_type: str = "PROFESSIONAL"  # PROFESSIONAL / GENERAL / STRESS
    skill_name: str
    text: str
    difficulty: str
    hints: Optional[str] = None
    time_limit_sec: int = 180
    source: str = "QUESTION_BANK"        # QUESTION_BANK / AI_GENERATED
    reference_points: List[str] = []     # 参考答案要点（仅复盘阶段下发）
    reveal_reference: bool = False       # 是否允许展示参考答案（作答中为 False）
    user_answer: Optional[str] = None
    evaluation: Optional[Dict[str, Any]] = None

class PaperPreviewItem(BaseModel):
    seq: int
    bank_id: Optional[int] = None      # 题库题目 ID，回传可按此考卷开考
    question_type: str
    skill_name: str
    stage: str
    difficulty: str
    text: str
    time_limit_sec: int
    source: str

class PaperPreviewOut(BaseModel):
    mode: str
    total_questions: int
    ratio: Dict[str, int]          # 题型配比（专业/通用/压力）
    allocated: Dict[str, int]      # 分配到的各题型题数
    from_bank: int                 # 题库命中题数
    missing_for_ai: Dict[str, int] = {}  # 题库缺口（将由 AI 补足）
    matched_category: str
    job_skills: List[str] = []
    bank_available: int
    questions: List[PaperPreviewItem] = []

class InterviewOut(BaseModel):
    version: int = 0
    report_state: str = "PENDING"
    learning_state: str = "PENDING"
    id: int
    user_id: int
    company_id: Optional[int] = None
    job_id: Optional[int] = None
    job_title: Optional[str] = None
    application_id: Optional[int] = None
    type: str
    mode: str
    difficulty: str
    status: str
    # 环节标记：OPENING 开场引导 / QA 逐题作答 / REVERSE 反问环节 / DONE 已进入结算
    phase: str = "QA"
    current_question_seq: int
    total_questions: int
    duration_minutes: int
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    created_at: datetime
    remaining_seconds: Optional[int] = None  # 服务端口径整场剩余秒数（未开始为 None）
    answered_count: int = 0                  # 已评分题数
    questions: List[InterviewQuestionOut] = []
    current_question: Optional[InterviewQuestionOut] = None

class InterviewAnswerRequest(BaseModel):
    question_id: int = Field(gt=0)
    request_id: str = Field(min_length=8, max_length=64, pattern=r"^[a-zA-Z0-9_-]+$")
    expected_version: Optional[int] = Field(default=None, ge=0)
    text: str = Field(max_length=20000)
    # 用时由服务端按呈现时间锚点计算，客户端值仅作无锚点时的回退
    duration_sec: Optional[int] = None
    skipped: bool = False  # 主动跳过本题（不同于空作答，不产生严厉评语）
    # 语音链路未接入：不再接收客户端假指标（speaking_rate/filler_count 已移除）

class AnswerEvaluationOut(BaseModel):
    provenance: Dict[str, Any] = {}
    version: int = 0
    report_state: str = "PENDING"
    # 环节标记：逐题作答结束后进入 REVERSE，前端据此切换到反问卡片
    phase: Optional[str] = None
    finished_qa: bool = False  # 逐题作答是否已全部结束（与 is_finished 同义，语义更明确）
    answer_id: int
    total_score: float
    dimensions: Dict[str, float]
    evidence: List[str]
    weaknesses: List[str]
    missing_knowledge: List[str]
    suggestions: List[str]
    next_action: str  # FOLLOW_UP, DEEP, BASIC, CHANGE_TOPIC, FINISH
    next_question: Optional[InterviewQuestionOut] = None
    is_followup: bool = False          # 下一题是否为 AI 评分触发的自适应追问题
    is_finished: bool = False          # 是否已答完全部题目（服务端判定）
    report_id: Optional[int] = None    # 自动结算生成的报告 ID
    remaining_seconds: Optional[int] = None  # 服务端口径的整场剩余秒数
    total_questions: Optional[int] = None    # 追问加题后的最新总题数
    # 单题超时（服务端判定）：超时轻扣分但不归零，空作答直接 0 分
    raw_score: Optional[float] = None
    overtime: bool = False
    overtime_sec: int = 0
    is_empty: bool = False
    is_skipped: bool = False  # 主动跳过，评语温和不影响能力画像

class ReverseQuestionOut(BaseModel):
    seq: int
    candidate_text: str
    ai_response: str
    evaluation: Dict[str, Any] = {}

class ReverseStateOut(BaseModel):
    """反问环节状态：用于面试间渲染反问卡片与历史问答。"""
    phase: str = "QA"
    max_count: int = 3
    used_count: int = 0
    remaining: int = 3
    questions: List[ReverseQuestionOut] = []

class ReverseSubmitRequest(BaseModel):
    text: str = Field(min_length=1, max_length=2000)

class InterviewReportOut(BaseModel):
    provenance: Dict[str, Any] = {}
    learning_state: str = "PENDING"
    id: int
    interview_id: int
    user_id: int
    job_title: Optional[str] = "Java后端开发工程师"
    interview_type: Optional[str] = "AI 全真模拟与能力复盘"
    duration_minutes: Optional[int] = 25
    total_score: float
    performance_level: str
    dimension_scores: Dict[str, float]
    strengths: List[str]
    weaknesses: List[str]
    suggestions: List[str]
    summary: str
    status: str
    created_at: datetime
    questions_analysis: List[Dict[str, Any]] = []
    # 时间维度分析：逐题用时/限时/超时情况与汇总（服务端计时口径）
    time_analysis: Optional[Dict[str, Any]] = None
    # 反问环节汇总（questions/answered_count/skipped/comment）；旧报告无此字段时为 None
    reverse_summary: Optional[Dict[str, Any]] = None

class InterviewInvitationCreate(BaseModel):
    application_id: int
    interview_id: Optional[int] = None
    note: Optional[str] = None
    days_valid: int = 7

class RecruiterEvaluationCreate(BaseModel):
    application_id: int
    interview_id: Optional[int] = None
    technical_score: float = 85.0
    project_score: float = 80.0
    problem_solving_score: float = 85.0
    communication_score: float = 90.0
    job_fit_score: float = 85.0
    summary: str
    recommendation: str = "PASS" # PASS, REVIEW, REJECT
