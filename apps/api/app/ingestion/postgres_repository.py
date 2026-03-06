"""PostgreSQL-backed account snapshot repository."""

from __future__ import annotations

from typing import Protocol

from .account_models import CanonicalAccountSnapshot


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


class PostgresAccountSnapshotRepository:
    """Repository adapter using PostgreSQL idempotency constraints."""

    def __init__(self, connection: SupportsConnection) -> None:
        self._connection = connection

    def insert_snapshot_if_new(self, snapshot: CanonicalAccountSnapshot) -> bool:
        sql = """
            INSERT INTO account_snapshots (
                tenant_id,
                connector_id,
                source_account_id,
                event_ts,
                current_balance,
                daily_pnl,
                account_currency,
                trading_is_disabled,
                starting_balance,
                daily_net_loss_limit
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT ON CONSTRAINT uq_account_snapshots_idempotency DO NOTHING
        """
        params = (
            snapshot.tenant_id,
            snapshot.connector_id,
            snapshot.source_account_id,
            snapshot.event_ts,
            snapshot.current_balance,
            snapshot.daily_pnl,
            snapshot.account_currency,
            snapshot.trading_is_disabled,
            snapshot.starting_balance,
            snapshot.daily_net_loss_limit,
        )

        with self._connection.cursor() as cursor:
            cursor.execute(sql, params)
            inserted = cursor.rowcount == 1

        self._connection.commit()
        return inserted

