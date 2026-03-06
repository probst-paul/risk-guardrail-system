import unittest

from fastapi.testclient import TestClient

from app.main import app, reset_account_snapshot_persistence_state
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


def _snapshot(event_ts: str, source_account_id: str = "acct-1001") -> dict:
    return {
        "tenant_id": "tenant-a",
        "connector_id": "sierra-chart-primary",
        "source_account_id": source_account_id,
        "event_ts": event_ts,
        "current_balance": "103500.25",
        "daily_pnl": "350.25",
        "account_currency": "USD",
        "trading_is_disabled": False,
    }


class ApiAccountSnapshotPersistenceIntegrationContractTest(unittest.TestCase):
    def setUp(self) -> None:
        reset_account_snapshot_persistence_state()
        self.client = TestClient(app)
        self.path = "/v1/accounts:snapshot"
        self.headers = {
            "Authorization": f"Bearer {_service_principal_token('tenant-a')}",
            "Content-Type": "application/json",
        }

    def test_snapshot_ingest_returns_persistence_counts(self) -> None:
        payload = {"snapshots": [_snapshot("2026-03-05T14:32:10Z", source_account_id="acct-a")]}
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
                _snapshot("2026-03-05T14:33:10Z", source_account_id="acct-b"),
            ]
        }
        response = self.client.post(self.path, json=payload, headers=self.headers)

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["total_count"], 3)
        self.assertEqual(body["persisted_count"], 2)
        self.assertEqual(body["duplicate_count"], 1)

    def test_snapshot_ingest_tracks_duplicates_across_requests(self) -> None:
        payload = {"snapshots": [_snapshot("2026-03-05T15:00:00Z", source_account_id="acct-c")]}

        first = self.client.post(self.path, json=payload, headers=self.headers)
        second = self.client.post(self.path, json=payload, headers=self.headers)

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)

        first_body = first.json()
        second_body = second.json()

        self.assertEqual(first_body["persisted_count"], 1)
        self.assertEqual(first_body["duplicate_count"], 0)
        self.assertEqual(second_body["persisted_count"], 0)
        self.assertEqual(second_body["duplicate_count"], 1)


if __name__ == "__main__":
    unittest.main()
