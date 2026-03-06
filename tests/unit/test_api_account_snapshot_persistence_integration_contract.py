import unittest

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


def _snapshot(event_ts: str) -> dict:
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


class ApiAccountSnapshotPersistenceIntegrationContractTest(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)
        self.path = "/v1/accounts:snapshot"
        self.headers = {
            "Authorization": f"Bearer {_service_principal_token('tenant-a')}",
            "Content-Type": "application/json",
        }

    def test_snapshot_ingest_returns_persistence_counts(self) -> None:
        payload = {"snapshots": [_snapshot("2026-03-05T14:32:10Z")]}
        response = self.client.post(self.path, json=payload, headers=self.headers)

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "accepted")
        self.assertEqual(body["total_count"], 1)
        self.assertEqual(body["persisted_count"], 1)
        self.assertEqual(body["duplicate_count"], 0)

    def test_snapshot_ingest_tracks_duplicates_in_same_batch(self) -> None:
        payload = {
            "snapshots": [
                _snapshot("2026-03-05T14:32:10Z"),
                _snapshot("2026-03-05T14:32:10Z"),
                _snapshot("2026-03-05T14:33:10Z"),
            ]
        }
        response = self.client.post(self.path, json=payload, headers=self.headers)

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["total_count"], 3)
        self.assertEqual(body["persisted_count"], 2)
        self.assertEqual(body["duplicate_count"], 1)


if __name__ == "__main__":
    unittest.main()
