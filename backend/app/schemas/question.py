from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, field_validator

QUESTION_TYPES = ("PROFESSIONAL", "GENERAL", "STRESS")
DIFFICULTIES = ("EASY", "MEDIUM", "HARD")


class QuestionBankItemOut(BaseModel):
    id: int
    job_category: str
    question_type: str
    skill_name: str
    stage: str
    difficulty: str
    text: str
    reference_points: List[str] = []
    hints: Optional[str] = None
    time_limit_sec: int
    source: str
    enabled: bool
    usage_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class QuestionBankUpsertRequest(BaseModel):
    """新建/编辑题库题目。编辑时未传字段保持原值（由端点处理）。"""
    job_category: str = Field(..., min_length=1, max_length=50)
    question_type: str = Field("PROFESSIONAL", max_length=20)
    skill_name: str = Field(..., min_length=1, max_length=100)
    stage: str = Field("专业基础", max_length=50)
    difficulty: str = Field("MEDIUM", max_length=20)
    text: str = Field(..., min_length=5, description="题干")
    reference_points: List[str] = Field(default_factory=list, description="参考答案要点")
    hints: Optional[str] = Field(None, max_length=255)
    time_limit_sec: int = Field(180, ge=30, le=1800)
    enabled: bool = True

    @field_validator("question_type")
    @classmethod
    def _check_type(cls, v: str) -> str:
        v = (v or "").upper()
        if v not in QUESTION_TYPES:
            raise ValueError(f"question_type 必须是 {'/'.join(QUESTION_TYPES)} 之一")
        return v

    @field_validator("difficulty")
    @classmethod
    def _check_diff(cls, v: str) -> str:
        v = (v or "").upper()
        if v not in DIFFICULTIES:
            raise ValueError(f"difficulty 必须是 {'/'.join(DIFFICULTIES)} 之一")
        return v

    @field_validator("text")
    @classmethod
    def _check_text(cls, v: str) -> str:
        v = (v or "").strip()
        if len(v) < 5:
            raise ValueError("题干内容过短")
        return v

    @field_validator("reference_points")
    @classmethod
    def _check_points(cls, v: List[str]) -> List[str]:
        # 过滤空项并去首尾空白；要点条数不做硬限制（管理端自行把握）
        return [p.strip() for p in (v or []) if p and p.strip()]


class QuestionBankToggleRequest(BaseModel):
    enabled: bool


# 审核动作 → 落库状态：approve 放行入卷，reject 驳回（永不入卷），pending 退回待审
REVIEW_STATUS_BY_ACTION = {"approve": "APPROVED", "reject": "REJECTED", "pending": "PENDING"}


class QuestionBankReviewRequest(BaseModel):
    """单题审核结论。"""
    action: str

    @field_validator("action")
    @classmethod
    def _check_action(cls, v: str) -> str:
        value = (v or "").strip().lower()
        if value not in REVIEW_STATUS_BY_ACTION:
            raise ValueError(f"action 必须是 {'/'.join(REVIEW_STATUS_BY_ACTION)} 之一")
        return value


class QuestionBankBatchReviewRequest(BaseModel):
    """按灌库批次批量审核（D5 分批放行）；可选再按岗位大类收窄范围。"""
    batch: str = Field(..., min_length=1, max_length=30)
    action: str
    job_category: Optional[str] = Field(None, max_length=50)

    @field_validator("action")
    @classmethod
    def _check_action(cls, v: str) -> str:
        value = (v or "").strip().lower()
        if value not in REVIEW_STATUS_BY_ACTION:
            raise ValueError(f"action 必须是 {'/'.join(REVIEW_STATUS_BY_ACTION)} 之一")
        return value
