import os
import unittest
from typing import Optional

from fastapi.testclient import TestClient

from app.main import app
from tests.helpers.auth_tokens import encode_test_token

try:
    import psycopg  # type: ignore
except Exception:  # noqa: BLE001
    psycopg = None


TEST_TENANT_ID = "11111111-1111-1111-1111-111111111111"


def _service_principal_token(tenant_id: str = TEST_TENANT_ID) -> str:
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
        "tenant_id": TEST_TENANT_ID,
        "connector_id": "sierra-chart-primary",
        "source_account_id": source_account_id,
        "event_ts": event_ts,
        "current_balance": "103500.25",
        "daily_pnl": "350.25",
        "account_currency": "USD",
        "trading_is_disabled": False,
    }


@unittest.skipUnless(os.getenv("DATABASE_URL"), "DATABASE_URL is required for postgres integration tests")
@unittest.skipUnless(psycopg is not None, "psycopg is required for postgres integration tests")
class ApiAccountSnapshotPostgresIntegrationContractTest(unittest.TestCase):
    def setUp(self) -> None:
        self.database_url = os.environ["DATABASE_URL"]
        self._ensure_schema_is_available()
        self._reset_db_state()
        self.client = TestClient(app)
        self.path = "/v1/accounts:snapshot"
        self.headers = {
            "Authorization": f"Bearer {_service_principal_token()}",
            "Content-Type": "application/json",
        }

    def _connect(self):
        return psycopg.connect(self.database_url)

    def _ensure_schema_is_available(self) -> None:
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT to_regclass('public.account_snapshots')")
                table_name: Optional[str] = cursor.fetchone()[0]
        if table_name != "account_snapshots":
            self.skipTest("account_snapshots table not found; run migrations before integration tests")

    def _reset_db_state(self) -> None:
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM account_snapshots WHERE tenant_id = %s::uuid",
                    (TEST_TENANT_ID,),
                )
                cursor.execute("DELETE FROM tenants WHERE id = %s::uuid", (TEST_TENANT_ID,))
                cursor.execute(
                    """
                    INSERT INTO tenants (id, slug, name, status)
                    VALUES (%s::uuid, %s, %s, %s)
                    """,
                    (
                        TEST_TENANT_ID,
                        "tenant-a",
                        "Tenant A",
                        "active",
                    ),
                )
            connection.commit()

    def test_first_ingest_persists_snapshot_in_postgres(self) -> None:
        response = self.client.post(
            self.path,
            json={"snapshots": [_snapshot("2026-03-05T14:32:10Z")]},
            headers=self.headers,
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["total_count"], 1)
        self.assertEqual(body["persisted_count"], 1)
        self.assertEqual(body["duplicate_count"], 0)

    def test_reingest_is_duplicate_safe_via_db_constraint(self) -> None:
        payload = {"snapshots": [_snapshot("2026-03-05T15:00:00Z")]}

        first = self.client.post(self.path, json=payload, headers=self.headers)
        second = self.client.post(self.path, json=payload, headers=self.headers)

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(first.json()["persisted_count"], 1)
        self.assertEqual(first.json()["duplicate_count"], 0)
        self.assertEqual(second.json()["persisted_count"], 0)
        self.assertEqual(second.json()["duplicate_count"], 1)

    def test_mixed_batch_counts_are_correct_against_real_postgres(self) -> None:
        self.client.post(
            self.path,
            json={"snapshots": [_snapshot("2026-03-05T16:00:00Z", source_account_id="acct-a")]},
            headers=self.headers,
        )

        payload = {
            "snapshots": [
                _snapshot("2026-03-05T16:00:00Z", source_account_id="acct-a"),
                _snapshot("2026-03-05T16:01:00Z", source_account_id="acct-b"),
            ]
        }
        response = self.client.post(self.path, json=payload, headers=self.headers)

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["total_count"], 2)
        self.assertEqual(body["persisted_count"], 1)
        self.assertEqual(body["duplicate_count"], 1)


if __name__ == "__main__":
    unittest.main()
