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


class _FakeCursor:
    def __init__(self) -> None:
        self.rowcount = 1

    def execute(self, _sql, _params) -> None:  # noqa: ANN001
        return None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):  # noqa: ANN001
        return False


class _FakeConnection:
    def __init__(self) -> None:
        self._cursor = _FakeCursor()
        self.close_called = False

    def cursor(self):
        return self._cursor

    def commit(self) -> None:
        return None

    def close(self) -> None:
        self.close_called = True


class ApiSnapshotDbLifecycleContractTest(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)
        self.path = "/v1/accounts:snapshot"
        self.headers = {
            "Authorization": f"Bearer {_service_principal_token('tenant-a')}",
            "Content-Type": "application/json",
        }

    @patch("app.main.get_db_connection")
    def test_snapshot_ingest_closes_db_connection_after_request(
        self, get_db_connection  # noqa: ANN001
    ) -> None:
        fake_connection = _FakeConnection()
        get_db_connection.return_value = fake_connection

        response = self.client.post(
            self.path,
            json=_snapshot_payload(),
            headers=self.headers,
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(fake_connection.close_called)


if __name__ == "__main__":
    unittest.main()
