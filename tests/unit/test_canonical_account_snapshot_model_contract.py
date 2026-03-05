import unittest
from decimal import Decimal

from app.ingestion.account_models import (
    CanonicalAccountSnapshot,
    CanonicalAccountValidationError,
    canonical_account_snapshot_from_dict,
)


class CanonicalAccountSnapshotModelContractTest(unittest.TestCase):
    def test_builds_snapshot_from_valid_payload(self) -> None:
        payload = {
            "tenant_id": "tenant-a",
            "connector_id": "sierra-chart-primary",
            "source_account_id": "acct-1001",
            "event_ts": "2026-03-05T14:32:10Z",
            "current_balance": "103500.25",
            "daily_pnl": "350.25",
            "account_currency": "USD",
            "trading_is_disabled": False,
        }

        snapshot = canonical_account_snapshot_from_dict(payload)

        self.assertIsInstance(snapshot, CanonicalAccountSnapshot)
        self.assertEqual(snapshot.tenant_id, "tenant-a")
        self.assertEqual(snapshot.connector_id, "sierra-chart-primary")
        self.assertEqual(snapshot.source_account_id, "acct-1001")
        self.assertEqual(snapshot.event_ts, "2026-03-05T14:32:10+00:00")
        self.assertEqual(snapshot.current_balance, Decimal("103500.25"))
        self.assertEqual(snapshot.daily_pnl, Decimal("350.25"))
        self.assertEqual(snapshot.account_currency, "USD")
        self.assertFalse(snapshot.trading_is_disabled)
        self.assertIsNone(snapshot.starting_balance)
        self.assertIsNone(snapshot.daily_net_loss_limit)

    def test_preserves_starting_balance_when_provided(self) -> None:
        payload = {
            "tenant_id": "tenant-a",
            "connector_id": "sierra-chart-primary",
            "source_account_id": "acct-1001",
            "event_ts": "2026-03-05T14:32:10Z",
            "current_balance": "103500.25",
            "daily_pnl": "350.25",
            "starting_balance": "103000.00",
            "account_currency": "USD",
            "trading_is_disabled": False,
            "daily_net_loss_limit": "1500.00",
        }

        snapshot = canonical_account_snapshot_from_dict(payload)

        self.assertEqual(snapshot.starting_balance, Decimal("103000.00"))
        self.assertEqual(snapshot.daily_net_loss_limit, Decimal("1500.00"))

    def test_rejects_missing_required_field(self) -> None:
        payload = {
            "tenant_id": "tenant-a",
            "connector_id": "sierra-chart-primary",
            "event_ts": "2026-03-05T14:32:10Z",
            "current_balance": "103500.25",
            "daily_pnl": "350.25",
            "account_currency": "USD",
            "trading_is_disabled": False,
        }

        with self.assertRaises(CanonicalAccountValidationError):
            canonical_account_snapshot_from_dict(payload)

    def test_rejects_non_positive_balance(self) -> None:
        payload = {
            "tenant_id": "tenant-a",
            "connector_id": "sierra-chart-primary",
            "source_account_id": "acct-1001",
            "event_ts": "2026-03-05T14:32:10Z",
            "current_balance": "0",
            "daily_pnl": "350.25",
            "account_currency": "USD",
            "trading_is_disabled": False,
        }

        with self.assertRaises(CanonicalAccountValidationError):
            canonical_account_snapshot_from_dict(payload)

    def test_rejects_timestamp_without_timezone(self) -> None:
        payload = {
            "tenant_id": "tenant-a",
            "connector_id": "sierra-chart-primary",
            "source_account_id": "acct-1001",
            "event_ts": "2026-03-05T14:32:10",
            "current_balance": "103500.25",
            "daily_pnl": "350.25",
            "account_currency": "USD",
            "trading_is_disabled": False,
        }

        with self.assertRaises(CanonicalAccountValidationError):
            canonical_account_snapshot_from_dict(payload)

    def test_rejects_missing_account_currency(self) -> None:
        payload = {
            "tenant_id": "tenant-a",
            "connector_id": "sierra-chart-primary",
            "source_account_id": "acct-1001",
            "event_ts": "2026-03-05T14:32:10Z",
            "current_balance": "103500.25",
            "daily_pnl": "350.25",
            "trading_is_disabled": False,
        }

        with self.assertRaises(CanonicalAccountValidationError):
            canonical_account_snapshot_from_dict(payload)

    def test_rejects_non_boolean_trading_is_disabled(self) -> None:
        payload = {
            "tenant_id": "tenant-a",
            "connector_id": "sierra-chart-primary",
            "source_account_id": "acct-1001",
            "event_ts": "2026-03-05T14:32:10Z",
            "current_balance": "103500.25",
            "daily_pnl": "350.25",
            "account_currency": "USD",
            "trading_is_disabled": "false",
        }

        with self.assertRaises(CanonicalAccountValidationError):
            canonical_account_snapshot_from_dict(payload)

if __name__ == "__main__":
    unittest.main()
