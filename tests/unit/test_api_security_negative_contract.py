import unittest

from fastapi.testclient import TestClient

from app.main import app
from tests.helpers.auth_tokens import encode_test_token


class ApiSecurityNegativeContractTest(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_admin_unlock_requires_authentication(self) -> None:
        response = self.client.post("/v1/admin/accounts/acct-1/unlock")
        self.assertEqual(response.status_code, 401)

    def test_admin_unlock_rejects_malformed_authorization_header(self) -> None:
        response = self.client.post(
            "/v1/admin/accounts/acct-1/unlock",
            headers={"Authorization": "Token not-a-bearer"},
        )
        self.assertEqual(response.status_code, 401)

    def test_admin_unlock_rejects_viewer_role(self) -> None:
        token = encode_test_token(
            {
                "sub": "user-123",
                "tenant_id": "tenant-a",
                "roles": ["viewer"],
                "principal_type": "user",
                "iss": "https://issuer.local",
                "aud": "risk-guardrail-api",
                "iat": 1762670400,
                "exp": 1920348800,
            }
        )
        response = self.client.post(
            "/v1/admin/accounts/acct-1/unlock",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 403)

    def test_admin_unlock_rejects_service_principal(self) -> None:
        token = encode_test_token(
            {
                "sub": "svc-1",
                "tenant_id": "tenant-a",
                "roles": ["service_principal"],
                "principal_type": "service_principal",
                "iss": "https://issuer.local",
                "aud": "risk-guardrail-api",
                "iat": 1762670400,
                "exp": 1920348800,
            }
        )
        response = self.client.post(
            "/v1/admin/accounts/acct-1/unlock",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 403)

    def test_ingestion_rejects_cross_tenant_override(self) -> None:
        token = encode_test_token(
            {
                "sub": "svc-1",
                "tenant_id": "tenant-a",
                "roles": ["service_principal"],
                "principal_type": "service_principal",
                "iss": "https://issuer.local",
                "aud": "risk-guardrail-api",
                "iat": 1762670400,
                "exp": 1920348800,
            }
        )
        response = self.client.post(
            "/v1/fills:ingest",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Tenant-Id": "tenant-b",
                "Content-Type": "application/json",
            },
            json={"fills": []},
        )
        self.assertEqual(response.status_code, 403)


if __name__ == "__main__":
    unittest.main()
