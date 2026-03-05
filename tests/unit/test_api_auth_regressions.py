import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from tests.helpers.auth_tokens import encode_test_token


def _base_claims() -> dict:
    return {
        "sub": "user-123",
        "tenant_id": "tenant-a",
        "roles": ["viewer"],
        "principal_type": "user",
        "iss": "https://issuer.local",
        "aud": "risk-guardrail-api",
        "iat": 1762670400,
        "exp": 1920348800,
    }


class ApiAuthRegressionTest(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_health_stays_unauthenticated(self) -> None:
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)

    def test_lowercase_bearer_prefix_is_rejected(self) -> None:
        token = encode_test_token(_base_claims())
        response = self.client.post(
            "/v1/admin/accounts/acct-1/unlock",
            headers={"Authorization": f"bearer {token}"},
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["detail"], "invalid_authorization")

    def test_bearer_prefix_with_extra_spaces_still_processes_token(self) -> None:
        token = encode_test_token(_base_claims())
        response = self.client.post(
            "/v1/admin/accounts/acct-1/unlock",
            headers={"Authorization": f"Bearer   {token}"},
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["detail"], "forbidden")

    def test_malformed_jwt_segment_count_returns_401(self) -> None:
        response = self.client.post(
            "/v1/admin/accounts/acct-1/unlock",
            headers={"Authorization": "Bearer only-two-segments.token"},
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["detail"], "invalid_token")

    def test_wrong_issuer_returns_401(self) -> None:
        claims = _base_claims()
        claims["iss"] = "https://wrong-issuer.local"
        token = encode_test_token(claims)
        response = self.client.post(
            "/v1/admin/accounts/acct-1/unlock",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["detail"], "invalid_token")

    def test_wrong_audience_returns_401(self) -> None:
        claims = _base_claims()
        claims["aud"] = "not-risk-guardrail-api"
        token = encode_test_token(claims)
        response = self.client.post(
            "/v1/admin/accounts/acct-1/unlock",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["detail"], "invalid_token")

    def test_missing_subject_returns_401(self) -> None:
        claims = _base_claims()
        claims.pop("sub")
        token = encode_test_token(claims)
        response = self.client.post(
            "/v1/admin/accounts/acct-1/unlock",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["detail"], "invalid_token")

    def test_missing_tenant_id_returns_401(self) -> None:
        claims = _base_claims()
        claims.pop("tenant_id")
        token = encode_test_token(claims)
        response = self.client.post(
            "/v1/admin/accounts/acct-1/unlock",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["detail"], "invalid_token")

    def test_future_iat_returns_401(self) -> None:
        claims = _base_claims()
        claims["iat"] = 2524608000
        token = encode_test_token(claims)
        response = self.client.post(
            "/v1/admin/accounts/acct-1/unlock",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["detail"], "invalid_token")

    def test_env_override_for_issuer_and_audience_is_enforced(self) -> None:
        custom_claims = _base_claims()
        custom_claims["iss"] = "https://custom-issuer.local"
        custom_claims["aud"] = "custom-risk-api"
        custom_token = encode_test_token(custom_claims)

        default_token = encode_test_token(_base_claims())
        with patch.dict(
            "os.environ",
            {"JWT_ISSUER": "https://custom-issuer.local", "JWT_AUDIENCE": "custom-risk-api"},
            clear=False,
        ):
            rejected = self.client.post(
                "/v1/admin/accounts/acct-1/unlock",
                headers={"Authorization": f"Bearer {default_token}"},
            )
            accepted_auth = self.client.post(
                "/v1/admin/accounts/acct-1/unlock",
                headers={"Authorization": f"Bearer {custom_token}"},
            )

        self.assertEqual(rejected.status_code, 401)
        self.assertEqual(rejected.json()["detail"], "invalid_token")
        self.assertEqual(accepted_auth.status_code, 403)
        self.assertEqual(accepted_auth.json()["detail"], "forbidden")


if __name__ == "__main__":
    unittest.main()
