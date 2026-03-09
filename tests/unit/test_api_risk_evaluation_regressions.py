import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from tests.helpers.auth_tokens import encode_test_token


def _service_principal_token(tenant_id: str = "tenant-a") -> str:
    claims = {
        "sub": "svc-1",
        "tenant_id": tenant_id,
        "roles": ["service_principal"],
        "principal_type": "service_principal",
        "iss": "https://issuer.local",
        "aud": "risk-guardrail-api",
        "iat": 1762670400,
        "exp": 1920348800,
    }
    return encode_test_token(claims)


def _payload(*, tenant_id: str, event_ts: str, daily_pnl: str) -> dict:
    return {
        "snapshot": {
            "tenant_id": tenant_id,
            "connector_id": "sierra-chart-primary",
            "source_account_id": "acct-1001",
            "event_ts": event_ts,
            "current_balance": "103500.25",
            "daily_pnl": daily_pnl,
            "daily_net_loss_limit": "1000.00",
            "account_currency": "USD",
            "trading_is_disabled": False,
        }
    }


class _NoopSnapshotService:
    def __init__(self) -> None:
        self.closed = False

    def persist_batch(self, _snapshots):  # noqa: ANN001
        return None

    def close(self) -> None:
        self.closed = True


class _FailingRiskService:
    def persist_if_new(self, *, snapshot, evaluation):  # noqa: ANN001
        raise RuntimeError("risk write failed")


class ApiRiskEvaluationRegressionTest(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)
        self.path = "/v1/risk:evaluate"
        self.headers = {
            "Authorization": f"Bearer {_service_principal_token('tenant-a')}",
            "Content-Type": "application/json",
        }

    def test_out_of_order_events_are_evaluated_without_stale_carryover(self) -> None:
        newer = self.client.post(
            self.path,
            json=_payload(
                tenant_id="tenant-a",
                event_ts="2026-03-10T21:59:00Z",
                daily_pnl="-1000.00",
            ),
            headers=self.headers,
        )
        older = self.client.post(
            self.path,
            json=_payload(
                tenant_id="tenant-a",
                event_ts="2026-03-10T20:59:00Z",
                daily_pnl="-100.00",
            ),
            headers=self.headers,
        )

        self.assertEqual(newer.status_code, 200)
        self.assertEqual(older.status_code, 200)
        self.assertEqual(newer.json()["risk_status"], "breached")
        self.assertEqual(older.json()["risk_status"], "active")

    def test_duplicate_event_re_evaluation_is_stable(self) -> None:
        payload = _payload(
            tenant_id="tenant-a",
            event_ts="2026-03-10T21:59:00Z",
            daily_pnl="-800.00",
        )

        first = self.client.post(self.path, json=payload, headers=self.headers)
        second = self.client.post(self.path, json=payload, headers=self.headers)

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(first.json()["risk_status"], second.json()["risk_status"])
        self.assertEqual(first.json()["trading_day"], second.json()["trading_day"])
        self.assertEqual(first.json()["loss_ratio"], second.json()["loss_ratio"])

    def test_cross_tenant_snapshot_payload_is_forbidden(self) -> None:
        response = self.client.post(
            self.path,
            json=_payload(
                tenant_id="tenant-b",
                event_ts="2026-03-10T21:59:00Z",
                daily_pnl="-100.00",
            ),
            headers=self.headers,
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["detail"], "forbidden")

    @patch("app.main._build_risk_persistence_services")
    def test_db_state_write_failure_does_not_break_risk_evaluation(
        self, build_services  # noqa: ANN001
    ) -> None:
        snapshot_service = _NoopSnapshotService()
        build_services.return_value = (snapshot_service, _FailingRiskService())

        response = self.client.post(
            self.path,
            json=_payload(
                tenant_id="tenant-a",
                event_ts="2026-03-10T21:59:00Z",
                daily_pnl="-100.00",
            ),
            headers=self.headers,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "evaluated")
        self.assertTrue(snapshot_service.closed)


if __name__ == "__main__":
    unittest.main()
