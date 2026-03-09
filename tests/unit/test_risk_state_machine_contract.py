import unittest
from decimal import Decimal

from app.ingestion.account_models import canonical_account_snapshot_from_dict
from app.risk.state_machine import evaluate_daily_risk_state


def _session_policy() -> dict:
    return {
        "timezone": "America/Chicago",
        "session_start_time": "17:00",
    }


def _snapshot(
    *,
    daily_pnl: str,
    daily_net_loss_limit: str | None,
    event_ts: str,
) -> dict:
    payload = {
        "tenant_id": "tenant-a",
        "connector_id": "sierra-chart-primary",
        "source_account_id": "acct-1001",
        "event_ts": event_ts,
        "current_balance": "103500.25",
        "daily_pnl": daily_pnl,
        "account_currency": "USD",
        "trading_is_disabled": False,
    }
    if daily_net_loss_limit is not None:
        payload["daily_net_loss_limit"] = daily_net_loss_limit
    return payload


class RiskStateMachineContractTest(unittest.TestCase):
    def test_returns_active_when_no_daily_net_loss_limit_is_present(self) -> None:
        snapshot = canonical_account_snapshot_from_dict(
            _snapshot(
                daily_pnl="-100.00",
                daily_net_loss_limit=None,
                event_ts="2026-03-10T14:30:00Z",
            )
        )

        result = evaluate_daily_risk_state(snapshot)

        self.assertEqual(result["status"], "active")
        self.assertIsNone(result["loss_ratio"])
        self.assertFalse(result["trading_locked"])

    def test_returns_warning_when_loss_ratio_reaches_warning_threshold(self) -> None:
        snapshot = canonical_account_snapshot_from_dict(
            _snapshot(
                daily_pnl="-800.00",
                daily_net_loss_limit="1000.00",
                event_ts="2026-03-10T14:31:00Z",
            )
        )

        result = evaluate_daily_risk_state(snapshot)

        self.assertEqual(result["status"], "warning")
        self.assertEqual(result["loss_ratio"], Decimal("0.8"))
        self.assertFalse(result["trading_locked"])

    def test_returns_breached_when_loss_ratio_reaches_or_exceeds_limit(self) -> None:
        snapshot = canonical_account_snapshot_from_dict(
            _snapshot(
                daily_pnl="-1000.00",
                daily_net_loss_limit="1000.00",
                event_ts="2026-03-10T14:32:00Z",
            )
        )

        result = evaluate_daily_risk_state(snapshot)

        self.assertEqual(result["status"], "breached")
        self.assertEqual(result["loss_ratio"], Decimal("1"))
        self.assertTrue(result["trading_locked"])

    def test_breached_state_is_sticky_within_same_trading_day(self) -> None:
        breach_snapshot = canonical_account_snapshot_from_dict(
            _snapshot(
                daily_pnl="-1000.00",
                daily_net_loss_limit="1000.00",
                event_ts="2026-03-10T23:30:00Z",
            )
        )
        recovered_snapshot = canonical_account_snapshot_from_dict(
            _snapshot(
                daily_pnl="-100.00",
                daily_net_loss_limit="1000.00",
                event_ts="2026-03-11T01:00:00Z",
            )
        )

        breached = evaluate_daily_risk_state(
            breach_snapshot,
            session_policy=_session_policy(),
        )
        same_day = evaluate_daily_risk_state(
            recovered_snapshot,
            previous_state=breached,
            session_policy=_session_policy(),
        )

        self.assertEqual(breached["status"], "breached")
        self.assertTrue(breached["trading_locked"])
        self.assertEqual(same_day["status"], "breached")
        self.assertTrue(same_day["trading_locked"])

    def test_breached_state_resets_on_new_trading_session(self) -> None:
        breach_snapshot = canonical_account_snapshot_from_dict(
            _snapshot(
                daily_pnl="-1000.00",
                daily_net_loss_limit="1000.00",
                event_ts="2026-03-10T21:59:00Z",
            )
        )
        next_session_snapshot = canonical_account_snapshot_from_dict(
            _snapshot(
                daily_pnl="-100.00",
                daily_net_loss_limit="1000.00",
                event_ts="2026-03-10T22:01:00Z",
            )
        )

        breached = evaluate_daily_risk_state(
            breach_snapshot,
            session_policy=_session_policy(),
        )
        next_session = evaluate_daily_risk_state(
            next_session_snapshot,
            previous_state=breached,
            session_policy=_session_policy(),
        )

        self.assertEqual(breached["status"], "breached")
        self.assertTrue(breached["trading_locked"])
        self.assertEqual(next_session["status"], "active")
        self.assertEqual(next_session["loss_ratio"], Decimal("0.1"))
        self.assertFalse(next_session["trading_locked"])

    def test_warning_state_resets_on_new_trading_session(self) -> None:
        warning_snapshot = canonical_account_snapshot_from_dict(
            _snapshot(
                daily_pnl="-800.00",
                daily_net_loss_limit="1000.00",
                event_ts="2026-03-10T21:59:00Z",
            )
        )
        next_session_snapshot = canonical_account_snapshot_from_dict(
            _snapshot(
                daily_pnl="-100.00",
                daily_net_loss_limit="1000.00",
                event_ts="2026-03-10T22:01:00Z",
            )
        )

        warning = evaluate_daily_risk_state(
            warning_snapshot,
            session_policy=_session_policy(),
        )
        next_session = evaluate_daily_risk_state(
            next_session_snapshot,
            previous_state=warning,
            session_policy=_session_policy(),
        )

        self.assertEqual(warning["status"], "warning")
        self.assertFalse(warning["trading_locked"])
        self.assertEqual(next_session["status"], "active")
        self.assertEqual(next_session["loss_ratio"], Decimal("0.1"))
        self.assertFalse(next_session["trading_locked"])


if __name__ == "__main__":
    unittest.main()
