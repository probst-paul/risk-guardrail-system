import unittest

from app.ingestion.account_models import canonical_account_snapshot_from_dict
from app.ingestion.persistence import (
    AccountSnapshotPersistenceService,
    PersistenceResult,
)


class _FakeSnapshotRepository:
    def __init__(self) -> None:
        self._seen_keys: set[tuple[str, str, str, str]] = set()
        self.calls = 0

    def insert_snapshot_if_new(self, snapshot) -> bool:  # noqa: ANN001
        self.calls += 1
        key = (
            snapshot.tenant_id,
            snapshot.connector_id,
            snapshot.source_account_id,
            snapshot.event_ts,
        )
        if key in self._seen_keys:
            return False
        self._seen_keys.add(key)
        return True


class _FailingSnapshotRepository:
    def insert_snapshot_if_new(self, snapshot) -> bool:  # noqa: ANN001
        raise RuntimeError("database unavailable")


def _snapshot_payload(event_ts: str = "2026-03-05T14:32:10Z") -> dict:
    return {
        "tenant_id": "tenant-a",
        "connector_id": "sierra-chart-primary",
        "source_account_id": "acct-1001",
        "event_ts": event_ts,
        "current_balance": "103500.25",
        "daily_pnl": "350.25",
        "account_currency": "USD",
        "trading_is_disabled": False,
    }


class AccountSnapshotPersistenceContractTest(unittest.TestCase):
    def test_persist_batch_returns_counts_for_new_and_duplicates(self) -> None:
        repository = _FakeSnapshotRepository()
        service = AccountSnapshotPersistenceService(repository)

        snapshots = [
            canonical_account_snapshot_from_dict(_snapshot_payload("2026-03-05T14:32:10Z")),
            canonical_account_snapshot_from_dict(_snapshot_payload("2026-03-05T14:32:10Z")),
            canonical_account_snapshot_from_dict(_snapshot_payload("2026-03-05T14:33:10Z")),
        ]

        result = service.persist_batch(snapshots)

        self.assertIsInstance(result, PersistenceResult)
        self.assertEqual(result.total_count, 3)
        self.assertEqual(result.persisted_count, 2)
        self.assertEqual(result.duplicate_count, 1)
        self.assertEqual(repository.calls, 3)

    def test_persist_batch_is_idempotent_on_repeat_calls(self) -> None:
        repository = _FakeSnapshotRepository()
        service = AccountSnapshotPersistenceService(repository)
        snapshot = canonical_account_snapshot_from_dict(_snapshot_payload())

        first = service.persist_batch([snapshot])
        second = service.persist_batch([snapshot])

        self.assertEqual(first.persisted_count, 1)
        self.assertEqual(first.duplicate_count, 0)
        self.assertEqual(second.persisted_count, 0)
        self.assertEqual(second.duplicate_count, 1)

    def test_persist_batch_handles_empty_input(self) -> None:
        repository = _FakeSnapshotRepository()
        service = AccountSnapshotPersistenceService(repository)

        result = service.persist_batch([])

        self.assertEqual(result.total_count, 0)
        self.assertEqual(result.persisted_count, 0)
        self.assertEqual(result.duplicate_count, 0)
        self.assertEqual(repository.calls, 0)

    def test_persist_batch_bubbles_repository_exceptions(self) -> None:
        repository = _FailingSnapshotRepository()
        service = AccountSnapshotPersistenceService(repository)
        snapshot = canonical_account_snapshot_from_dict(_snapshot_payload())

        with self.assertRaisesRegex(RuntimeError, "database unavailable"):
            service.persist_batch([snapshot])


if __name__ == "__main__":
    unittest.main()
