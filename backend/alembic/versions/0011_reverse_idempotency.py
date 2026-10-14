"""反问环节幂等加固：新增 request_id 幂等键与两个唯一索引。

背景：逐题作答有 request_id 幂等 + 租约 CAS 保护，反问却两者皆无——`seq` 由 count()
推导，并发两次提交会各自读到 0 并插入两条 seq=1，网络超时重发与刷新后重提同样重复入库。
本迁移先清洗历史重复（同一 (interview_id, seq) 只保留最早一条），再建唯一索引作为兜底。
"""
from alembic import op
import sqlalchemy as sa
from app.core.database import Base
import app.models

revision = "0011_reverse_idempotency"
down_revision = "0010_reverse_questions"
branch_labels = None
depends_on = None

TABLE = "interview_reverse_questions"
# 用唯一索引而非表级唯一约束：SQLite 下约束需要整表重建，索引在两种方言都可直接 ALTER
UNIQUE_INDEXES = {
    "uq_reverse_interview_seq": ["interview_id", "seq"],
    "uq_reverse_interview_request": ["interview_id", "request_id"],
}


def upgrade():
    conn = op.get_bind()
    # 新库首次升级时按模型定义建表（已含 request_id 与唯一索引）
    Base.metadata.create_all(conn)
    inspector = sa.inspect(conn)
    if TABLE not in inspector.get_table_names():
        return
    if "request_id" not in {c["name"] for c in inspector.get_columns(TABLE)}:
        op.add_column(TABLE, sa.Column("request_id", sa.String(64), nullable=True))

    # 唯一索引不能建立在仍有重复的数据上：保留每组 (interview_id, seq) 中 id 最小的一条
    conn.execute(sa.text(
        f"DELETE FROM {TABLE} WHERE id NOT IN ("
        f"SELECT id FROM (SELECT MIN(id) AS id FROM {TABLE} GROUP BY interview_id, seq) AS keep_rows)"
    ))

    indexed = {i["name"] for i in sa.inspect(conn).get_indexes(TABLE)}
    for name, columns in UNIQUE_INDEXES.items():
        if name not in indexed:
            op.create_index(name, TABLE, columns, unique=True)


def downgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if TABLE not in inspector.get_table_names():
        return
    indexed = {i["name"] for i in inspector.get_indexes(TABLE)}
    for name in UNIQUE_INDEXES:
        if name in indexed:
            op.drop_index(name, table_name=TABLE)
    if "request_id" in {c["name"] for c in inspector.get_columns(TABLE)}:
        op.drop_column(TABLE, "request_id")
