"""Add account snapshots table with idempotency constraints.

Revision ID: 20260306_0002
Revises: 20260305_0001
Create Date: 2026-03-06
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260306_0002"
down_revision = "20260305_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "account_snapshots",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("connector_id", sa.String(length=80), nullable=False),
        sa.Column("source_account_id", sa.String(length=120), nullable=False),
        sa.Column("event_ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("current_balance", sa.Numeric(18, 6), nullable=False),
        sa.Column("daily_pnl", sa.Numeric(18, 6), nullable=False),
        sa.Column("account_currency", sa.String(length=16), nullable=False),
        sa.Column("trading_is_disabled", sa.Boolean(), nullable=False),
        sa.Column("starting_balance", sa.Numeric(18, 6), nullable=True),
        sa.Column("daily_net_loss_limit", sa.Numeric(18, 6), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint(
            "tenant_id",
            "connector_id",
            "source_account_id",
            "event_ts",
            name="uq_account_snapshots_idempotency",
        ),
    )
    # idempotency key columns: tenant_id connector_id source_account_id event_ts
    op.create_index("ix_account_snapshots_tenant_id", "account_snapshots", ["tenant_id"])
    op.create_index(
        "ix_account_snapshots_connector_account",
        "account_snapshots",
        ["connector_id", "source_account_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_account_snapshots_connector_account", table_name="account_snapshots")
    op.drop_index("ix_account_snapshots_tenant_id", table_name="account_snapshots")
    op.drop_table("account_snapshots")

