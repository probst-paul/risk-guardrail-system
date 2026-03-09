"""Add risk state snapshots table linked to ingested account snapshots.

Revision ID: 20260309_0003
Revises: 20260306_0002
Create Date: 2026-03-09
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260309_0003"
down_revision = "20260306_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "risk_state_snapshots",
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
        sa.Column("trading_day", sa.Date(), nullable=False),
        sa.Column("risk_status", sa.String(length=16), nullable=False),
        sa.Column("trading_locked", sa.Boolean(), nullable=False),
        sa.Column("loss_ratio", sa.Numeric(18, 6), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "connector_id", "source_account_id", "event_ts"],
            [
                "account_snapshots.tenant_id",
                "account_snapshots.connector_id",
                "account_snapshots.source_account_id",
                "account_snapshots.event_ts",
            ],
            name="fk_risk_state_snapshots_account_snapshot",
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint(
            "risk_status IN ('active', 'warning', 'breached')",
            name="ck_risk_state_snapshots_status",
        ),
        sa.UniqueConstraint(
            "tenant_id",
            "connector_id",
            "source_account_id",
            "event_ts",
            name="uq_risk_state_snapshots_source_event",
        ),
    )
    op.create_index(
        "ix_risk_state_snapshots_tenant_trading_day",
        "risk_state_snapshots",
        ["tenant_id", "trading_day"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_risk_state_snapshots_tenant_trading_day",
        table_name="risk_state_snapshots",
    )
    op.drop_table("risk_state_snapshots")

