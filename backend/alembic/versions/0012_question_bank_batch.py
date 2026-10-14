"""题库批次标注 + 审核闸门回补（D3、D5）。

给 question_bank 增加 batch 列，按题干把种子数据归入灌库批次，让管理端能「按批次放行」。
同时按 D3 的决定把 P0-3a/3b/3c 共 179 题与本次新增的 P0-4 一律置为 PENDING——
审核闸门要对出题人本人生效；历史批次（P0-CORE / P0-NONTECH 共 118 题）保持 APPROVED，
不至于整库瞬间组不出卷。
"""
from alembic import op
import sqlalchemy as sa
from app.core.database import Base
import app.models
from app.data.question_bank import BATCH_REVIEW_POLICY, QUESTION_BANK_SEED

revision = "0012_question_bank_batch"
down_revision = "0011_reverse_idempotency"
branch_labels = None
depends_on = None

TABLE = "question_bank"
COLUMN = "batch"
INDEX = "ix_question_bank_batch"
# 需要走审核闸门的批次：策略里非 APPROVED 的那些
GATED_BATCHES = tuple(batch for batch, status in BATCH_REVIEW_POLICY.items() if status != "APPROVED")


def _text_to_batch():
    mapping = {}
    for item in QUESTION_BANK_SEED:
        text = (item.get("text") or "").strip()
        if text:
            mapping[text] = item["batch"]
    return mapping


def upgrade():
    conn = op.get_bind()
    Base.metadata.create_all(conn)
    inspector = sa.inspect(conn)
    if TABLE not in inspector.get_table_names():
        return
    if COLUMN not in {c["name"] for c in inspector.get_columns(TABLE)}:
        op.add_column(TABLE, sa.Column(COLUMN, sa.String(30), nullable=True))
    if INDEX not in {i["name"] for i in sa.inspect(conn).get_indexes(TABLE)}:
        op.create_index(INDEX, TABLE, [COLUMN])

    # 按题干回填批次：只标注种子题目，人工新增题保持 NULL 由管理端逐条判断
    mapping = _text_to_batch()
    rows = conn.execute(sa.text(f"SELECT id, text FROM {TABLE}")).fetchall()
    for row in rows:
        batch = mapping.get((row.text or "").strip())
        if batch:
            conn.execute(sa.text(f"UPDATE {TABLE} SET batch = :batch WHERE id = :id"),
                         {"batch": batch, "id": row.id})

    # D3：新批次重新回到待审状态，由管理端按批次放行
    for batch in GATED_BATCHES:
        conn.execute(sa.text(
            f"UPDATE {TABLE} SET review_status = 'PENDING' WHERE batch = :batch"
        ), {"batch": batch})


def downgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if TABLE not in inspector.get_table_names():
        return
    # 撤销本次回补的送审状态（不撤销管理端后续做的真实审核，只恢复被本迁移置为 PENDING 的行）
    for batch in GATED_BATCHES:
        conn.execute(sa.text(
            f"UPDATE {TABLE} SET review_status = 'APPROVED' WHERE batch = :batch AND review_status = 'PENDING'"
        ), {"batch": batch})
    if INDEX in {i["name"] for i in inspector.get_indexes(TABLE)}:
        op.drop_index(INDEX, table_name=TABLE)
    if COLUMN in {c["name"] for c in inspector.get_columns(TABLE)}:
        op.drop_column(TABLE, COLUMN)
