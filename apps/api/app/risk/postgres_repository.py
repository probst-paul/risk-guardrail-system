"""PostgreSQL-backed repository for risk-state snapshots."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Protocol

from .persistence import RiskStateSnapshot


class SupportsCursor(Protocol):
    rowcount: int

    def execute(self, sql: str, params: tuple) -> None:
        ...

    def __enter__(self) -> "SupportsCursor":
        ...

    def __exit__(self, exc_type, exc, tb) -> bool:  # noqa: ANN001
        ...


class SupportsConnection(Protocol):
    def cursor(self) -> SupportsCursor:
        ...

    def commit(self) -> None:
        ...


class PostgresRiskStateRepository:
    """Repository adapter using PostgreSQL idempotency constraints."""

    def __init__(self, connection: SupportsConnection) -> None:
        self._connection = connection

    def insert_state_if_new(self, state: RiskStateSnapshot) -> bool:
        sql = """
            INSERT INTO risk_state_snapshots (
                tenant_id,
                connector_id,
                source_account_id,
                event_ts,
                trading_day,
                risk_status,
                trading_locked,
                loss_ratio
            )
            VALUES (%s::uuid, %s, %s, %s, %s::date, %s, %s, %s)
            ON CONFLICT ON CONSTRAINT uq_risk_state_snapshots_source_event DO NOTHING
        """
        params = (
            state.tenant_id,
            state.connector_id,
            state.source_account_id,
            state.event_ts,
            state.trading_day,
            state.risk_status,
            state.trading_locked,
            _to_numeric_param(state.loss_ratio),
        )

        with self._connection.cursor() as cursor:
            cursor.execute(sql, params)
            inserted = cursor.rowcount == 1

        self._connection.commit()
        return inserted


def _to_numeric_param(value: Decimal | None) -> str | None:
    if value is None:
        return None
    return str(value)

