"""反问环节：新增 interview_reverse_questions 表与报告反问汇总字段。

与逐题作答分表存放：反问问答不进 rubric 总分，只作为报告"反问表现"的素材，
这样既补齐真实面试流程，也不会变相惩罚内向型候选人。
"""
from alembic import op
import sqlalchemy as sa
from app.core.database import Base
import app.models

revision = "0010_reverse_questions"
down_revision = "0009_interview_phase"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    # 新表由模型定义直接创建（含全部字段与索引）
    Base.metadata.create_all(conn)
    columns = {
        "interview_reports": [sa.Column("reverse_summary_json", sa.Text())],
    }
    for table, additions in columns.items():
        existing = {c["name"] for c in sa.inspect(conn).get_columns(table)}
        for column in additions:
            if column.name not in existing:
                op.add_column(table, column)


def downgrade():
    conn = op.get_bind()
    existing = {c["name"] for c in sa.inspect(conn).get_columns("interview_reports")}
    if "reverse_summary_json" in existing:
        op.drop_column("interview_reports", "reverse_summary_json")
    if "interview_reverse_questions" in sa.inspect(conn).get_table_names():
        op.drop_table("interview_reverse_questions")