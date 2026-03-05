import unittest
from datetime import datetime, timedelta, timezone

from app.auth.authorization import is_authorized
from app.auth.identity import RequestIdentity, identity_from_claims
from app.auth.jwt import JwtValidationError, validate_registered_claims


class AuthPrimitivesContractTest(unittest.TestCase):
    def test_identity_from_claims_builds_request_identity(self) -> None:
        claims = {
            "sub": "user-123",
            "tenant_id": "tenant-a",
            "roles": ["viewer", "risk_admin"],
            "principal_type": "user",
        }

        identity = identity_from_claims(claims)

        self.assertIsInstance(identity, RequestIdentity)
        self.assertEqual(identity.subject, "user-123")
        self.assertEqual(identity.tenant_id, "tenant-a")
        self.assertEqual(identity.principal_type, "user")
        self.assertEqual(identity.roles, frozenset({"viewer", "risk_admin"}))

    def test_validate_registered_claims_rejects_expired_token(self) -> None:
        now = datetime(2026, 3, 5, 12, 0, tzinfo=timezone.utc)
        claims = {
            "sub": "user-123",
            "tenant_id": "tenant-a",
            "iss": "https://issuer.local",
            "aud": "risk-guardrail-api",
            "iat": int((now - timedelta(minutes=30)).timestamp()),
            "exp": int((now - timedelta(minutes=1)).timestamp()),
        }

        with self.assertRaises(JwtValidationError):
            validate_registered_claims(
                claims, expected_issuer="https://issuer.local", expected_audience="risk-guardrail-api", now=now
            )

    def test_validate_registered_claims_accepts_valid_claims(self) -> None:
        now = datetime(2026, 3, 5, 12, 0, tzinfo=timezone.utc)
        claims = {
            "sub": "user-123",
            "tenant_id": "tenant-a",
            "iss": "https://issuer.local",
            "aud": "risk-guardrail-api",
            "iat": int((now - timedelta(minutes=1)).timestamp()),
            "exp": int((now + timedelta(minutes=30)).timestamp()),
        }

        validate_registered_claims(
            claims, expected_issuer="https://issuer.local", expected_audience="risk-guardrail-api", now=now
        )

    def test_authorization_defaults_to_deny_without_required_roles(self) -> None:
        identity = RequestIdentity(
            subject="user-123",
            tenant_id="tenant-a",
            roles=frozenset({"viewer"}),
            principal_type="user",
        )

        self.assertFalse(is_authorized(identity, required_roles=[]))

    def test_authorization_allows_when_role_matches(self) -> None:
        identity = RequestIdentity(
            subject="user-123",
            tenant_id="tenant-a",
            roles=frozenset({"risk_admin"}),
            principal_type="user",
        )

        self.assertTrue(is_authorized(identity, required_roles=["risk_admin"]))


if __name__ == "__main__":
    unittest.main()
