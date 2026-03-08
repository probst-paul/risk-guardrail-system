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


def _snapshot_payload() -> dict:
    return {
        "snapshots": [
            {
                "tenant_id": "tenant-a",
                "connector_id": "sierra-chart-primary",
                "source_account_id": "acct-1001",
                "event_ts": "2026-03-05T14:32:10Z",
                "current_balance": "103500.25",
                "daily_pnl": "350.25",
                "account_currency": "USD",
                "trading_is_disabled": False,
            }
        ]
    }


class ApiSnapshotPersistenceAvailabilityContractTest(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)
        self.path = "/v1/accounts:snapshot"
        self.headers = {
            "Authorization": f"Bearer {_service_principal_token('tenant-a')}",
            "Content-Type": "application/json",
        }

    @patch("app.main.get_db_connection", return_value=None)
    def test_snapshot_ingest_returns_503_when_db_connection_unavailable(
        self, _get_db_connection  # noqa: ANN001
    ) -> None:
        response = self.client.post(
            self.path,
            json=_snapshot_payload(),
            headers=self.headers,
        )

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["detail"], "persistence_unavailable")

    @patch("app.main.get_db_connection", return_value=object())
    def test_snapshot_ingest_returns_503_for_invalid_db_connection_object(
        self, _get_db_connection  # noqa: ANN001
    ) -> None:
        response = self.client.post(
            self.path,
            json=_snapshot_payload(),
            headers=self.headers,
        )

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["detail"], "persistence_unavailable")


if __name__ == "__main__":
    unittest.main()
