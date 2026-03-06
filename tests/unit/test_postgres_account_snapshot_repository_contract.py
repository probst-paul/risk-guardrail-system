import unittest
from typing import Optional

from app.ingestion.account_models import canonical_account_snapshot_from_dict
from app.ingestion.postgres_repository import PostgresAccountSnapshotRepository


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


def _snapshot() -> dict:
    return {
        "tenant_id": "tenant-a",
        "connector_id": "sierra-chart-primary",
        "source_account_id": "acct-1001",
        "event_ts": "2026-03-05T14:32:10Z",
        "current_balance": "103500.25",
        "daily_pnl": "350.25",
        "account_currency": "USD",
        "trading_is_disabled": False,
    }


class PostgresAccountSnapshotRepositoryContractTest(unittest.TestCase):
    def test_insert_new_snapshot_returns_true(self) -> None:
        cursor = _FakeCursor(rowcount=1)
        connection = _FakeConnection(cursor)
        repository = PostgresAccountSnapshotRepository(connection)

        result = repository.insert_snapshot_if_new(
            canonical_account_snapshot_from_dict(_snapshot())
        )

        self.assertTrue(result)
        self.assertTrue(connection.committed)
        self.assertIsNotNone(cursor.sql)
        self.assertIn("INSERT INTO account_snapshots", cursor.sql)
        self.assertIn("ON CONFLICT ON CONSTRAINT uq_account_snapshots_idempotency DO NOTHING", cursor.sql)

    def test_insert_duplicate_snapshot_returns_false(self) -> None:
        cursor = _FakeCursor(rowcount=0)
        connection = _FakeConnection(cursor)
        repository = PostgresAccountSnapshotRepository(connection)

        result = repository.insert_snapshot_if_new(
            canonical_account_snapshot_from_dict(_snapshot())
        )

        self.assertFalse(result)
        self.assertTrue(connection.committed)

    def test_insert_bubbles_unexpected_database_errors(self) -> None:
        cursor = _FakeCursor(exc=RuntimeError("db unavailable"))
        connection = _FakeConnection(cursor)
        repository = PostgresAccountSnapshotRepository(connection)

        with self.assertRaisesRegex(RuntimeError, "db unavailable"):
            repository.insert_snapshot_if_new(canonical_account_snapshot_from_dict(_snapshot()))


if __name__ == "__main__":
    unittest.main()
