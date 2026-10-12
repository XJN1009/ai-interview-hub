"""面试环节标记：新增 interviews.phase，用于区分开场引导 / 逐题作答 / 反问环节。

背景：模拟面试此前缺少"开场"与"反问"两个真实面试必备环节。为不扰动既有状态机
（status 仍负责 CREATED→READY→IN_PROGRESS→COMPLETED 的迁移与 409 拦截），
这里用独立字段表达环节，start/pause/resume/abort 的合法性判断完全不变。

既有会话一律回填为 QA：它们已经越过开场，若默认成 OPENING 会让旧记录重新打开时
突然出现开场卡片，属于行为突变。
"""
from alembic import op
import sqlalchemy as sa
from app.core.database import Base
import app.models

revision = "0009_interview_phase"
down_revision = "0008_question_bank_relevance"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    # 先补齐缺失的表（新库首次升级时按模型定义建表，已含 phase 字段）
    Base.metadata.create_all(conn)
    columns = {
        "interviews": [
            sa.Column("phase", sa.String(20), nullable=False, server_default="QA"),
        ],
    }
    for table, additions in columns.items():
        existing = {c["name"] for c in sa.inspect(conn).get_columns(table)}
        for column in additions:
            if column.name not in existing:
                op.add_column(table, column)


def downgrade():
    # 仅移除环节标记，面试记录与评分结果不受影响
    conn = op.get_bind()
    existing = {c["name"] for c in sa.inspect(conn).get_columns("interviews")}
    if "phase" in existing:
        op.drop_column("interviews", "phase")