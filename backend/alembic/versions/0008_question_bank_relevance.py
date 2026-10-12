"""题库相关性治理：新增技能别名与应用审核状态，收紧组卷取题范围。

背景：组卷此前在专业题不足时会跨岗位大类借题（"不限大类"兜底 + 跨题型借用），
导致非技术岗/小大类卷面冒出后端 Java 等跨岗位陈题；技能匹配也只靠子串判断。
本迁移只增加字段，不改动既有题目内容，历史卷面与报表不受影响。
"""
from alembic import op
import sqlalchemy as sa
from app.core.database import Base
import app.models

revision = "0008_question_bank_relevance"
down_revision = "0007_resume_documents"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    # 先补齐缺失的表（新库首次升级时 question_bank 尚不存在，直接建表即含新字段）
    Base.metadata.create_all(conn)
    columns = {
        "question_bank": [
            sa.Column("aliases", sa.String(255)),
            # 既有题目均视为已审，避免升级后题库被整体排除在组卷之外
            sa.Column("review_status", sa.String(20), nullable=False, server_default="APPROVED"),
        ],
    }
    for table, additions in columns.items():
        existing = {c["name"] for c in sa.inspect(conn).get_columns(table)}
        for column in additions:
            if column.name not in existing:
                op.add_column(table, column)


def downgrade():
    # 仅移除本迁移新增的字段，题目内容与历史卷面不受影响
    conn = op.get_bind()
    existing = {c["name"] for c in sa.inspect(conn).get_columns("question_bank")}
    for name in ("aliases", "review_status"):
        if name in existing:
            op.drop_column("question_bank", name)