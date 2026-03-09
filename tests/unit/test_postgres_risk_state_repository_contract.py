import unittest
from decimal import Decimal
from typing import Optional

from app.risk.persistence import RiskStateSnapshot
from app.risk.postgres_repository import PostgresRiskStateRepository


class _FakeCursor:
    def __init__(self, rowcount: int = 1, exc: Optional[Exception] = None) -> None:
        self.rowcount = rowcount
        self.exc = exc
        self.sql = None
        self.params = None

    def execute(self, sql, params):  # noqa: ANN001
        self.sql = sql
        self.params = params
        if self.exc:
            raise self.exc

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):  # noqa: ANN001
        return False


class _FakeConnection:
    def __init__(self, cursor: _FakeCursor) -> None:
        self._cursor = cursor
        self.committed = False

    def cursor(self):
        return self._cursor

    def commit(self) -> None:
        self.committed = True


def _state() -> RiskStateSnapshot:
    return RiskStateSnapshot(
        tenant_id="11111111-1111-1111-1111-111111111111",
        connector_id="sierra-chart-primary",
        source_account_id="acct-1001",
        event_ts="2026-03-10T21:59:00+00:00",
        trading_day="2026-03-10",
        risk_status="warning",
        trading_locked=False,
        loss_ratio=Decimal("0.8"),
    )


class PostgresRiskStateRepositoryContractTest(unittest.TestCase):
    def test_insert_new_state_returns_true(self) -> None:
        cursor = _FakeCursor(rowcount=1)
        connection = _FakeConnection(cursor)
        repository = PostgresRiskStateRepository(connection)

        result = repository.insert_state_if_new(_state())

        self.assertTrue(result)
        self.assertTrue(connection.committed)
        self.assertIn("INSERT INTO risk_state_snapshots", cursor.sql)
        self.assertIn(
            "ON CONFLICT ON CONSTRAINT uq_risk_state_snapshots_source_event DO NOTHING",
            cursor.sql,
        )

    def test_insert_duplicate_state_returns_false(self) -> None:
        cursor = _FakeCursor(rowcount=0)
        connection = _FakeConnection(cursor)
        repository = PostgresRiskStateRepository(connection)

        result = repository.insert_state_if_new(_state())

        self.assertFalse(result)
        self.assertTrue(connection.committed)

    def test_insert_bubbles_unexpected_database_errors(self) -> None:
        cursor = _FakeCursor(exc=RuntimeError("db unavailable"))
        connection = _FakeConnection(cursor)
        repository = PostgresRiskStateRepository(connection)

        with self.assertRaisesRegex(RuntimeError, "db unavailable"):
            repository.insert_state_if_new(_state())


if __name__ == "__main__":
    unittest.main()
