"""反问环节改为纯记录：删除 ai_response 与 evaluation_json 两列。

背景：D1 把反问定为"零成本"环节，成本不只是分数与时长——每条提问原本都要
等一次 `answer_reverse_question` 的 LLM 调用（无 Key 时还会落进 mock 兜底文案，
等于把编造的面试官回答写进记录）。本迁移让数据模型与"AI 不作答"的语义一致，
反问表只保留候选人提问本身。

历史数据：`interview_reports.reverse_summary_json` 里的旧快照是自包含文本，不读这两列，
因此删除列不影响已生成报告的展示。降级只能把列加回为空，无法还原已丢弃的回答。
"""
from alembic import op
import sqlalchemy as sa
from app.core.database import Base
import app.models

revision = "0013_reverse_record_only"
down_revision = "0012_question_bank_batch"
branch_labels = None
depends_on = None

TABLE = "interview_reverse_questions"
DROP_COLUMNS = ["ai_response", "evaluation_json"]


def upgrade():
    conn = op.get_bind()
    # 新库首次升级时按模型建表，本就不含这两列
    Base.metadata.create_all(conn)
    inspector = sa.inspect(conn)
    if TABLE not in inspector.get_table_names():
        return
    existing = {c["name"] for c in inspector.get_columns(TABLE)}
    for column in DROP_COLUMNS:
        if column in existing:
            op.drop_column(TABLE, column)


def downgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if TABLE not in inspector.get_table_names():
        return
    existing = {c["name"] for c in inspector.get_columns(TABLE)}
    if "ai_response" not in existing:
        op.add_column(TABLE, sa.Column("ai_response", sa.Text(), nullable=True))
    if "evaluation_json" not in existing:
        op.add_column(TABLE, sa.Column("evaluation_json", sa.Text(), nullable=True))
