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


def _valid_snapshot_payload() -> dict:
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


class ApiAccountSnapshotIngestContractTest(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)
        self.path = "/v1/accounts:snapshot"

    def test_snapshot_ingest_requires_authentication(self) -> None:
        response = self.client.post(self.path, json=_valid_snapshot_payload())
        self.assertEqual(response.status_code, 401)

    def test_snapshot_ingest_rejects_cross_tenant_override(self) -> None:
        token = _service_principal_token(tenant_id="tenant-a")
        response = self.client.post(
            self.path,
            json=_valid_snapshot_payload(),
            headers={
                "Authorization": f"Bearer {token}",
                "X-Tenant-Id": "tenant-b",
                "Content-Type": "application/json",
            },
        )
        self.assertEqual(response.status_code, 403)

    def test_snapshot_ingest_accepts_valid_authenticated_payload(self) -> None:
        token = _service_principal_token(tenant_id="tenant-a")
        response = self.client.post(
            self.path,
            json=_valid_snapshot_payload(),
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "accepted")
        self.assertEqual(body["tenant_id"], "tenant-a")
        self.assertEqual(body["accepted_count"], 1)

    def test_snapshot_ingest_rejects_invalid_snapshot_payload(self) -> None:
        token = _service_principal_token(tenant_id="tenant-a")
        payload = _valid_snapshot_payload()
        payload["snapshots"][0].pop("account_currency")

        response = self.client.post(
            self.path,
            json=payload,
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        )
        self.assertIn(response.status_code, (400, 422))


if __name__ == "__main__":
    unittest.main()
