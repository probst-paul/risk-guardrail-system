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


def _viewer_token(tenant_id: str = "tenant-a") -> str:
    claims = {
        "sub": "user-1",
        "tenant_id": tenant_id,
        "roles": ["viewer"],
        "principal_type": "user",
        "iss": "https://issuer.local",
        "aud": "risk-guardrail-api",
        "iat": 1762670400,
        "exp": 1920348800,
    }
    return encode_test_token(claims)


def _valid_payload(tenant_id: str = "tenant-a") -> dict:
    return {
        "snapshot": {
            "tenant_id": tenant_id,
            "connector_id": "sierra-chart-primary",
            "source_account_id": "acct-1001",
            "event_ts": "2026-03-10T21:59:00Z",
            "current_balance": "103500.25",
            "daily_pnl": "-100.00",
            "daily_net_loss_limit": "1000.00",
            "account_currency": "USD",
            "trading_is_disabled": False,
        }
    }


class ApiRiskEvaluationContractTest(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)
        self.path = "/v1/risk:evaluate"

    def test_risk_evaluation_requires_authentication(self) -> None:
        response = self.client.post(self.path, json=_valid_payload())
        self.assertEqual(response.status_code, 401)

    def test_risk_evaluation_rejects_non_service_principal_role(self) -> None:
        token = _viewer_token("tenant-a")
        response = self.client.post(
            self.path,
            json=_valid_payload(),
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["detail"], "forbidden")

    def test_risk_evaluation_rejects_cross_tenant_override(self) -> None:
        token = _service_principal_token("tenant-a")
        response = self.client.post(
            self.path,
            json=_valid_payload(tenant_id="tenant-a"),
            headers={
                "Authorization": f"Bearer {token}",
                "X-Tenant-Id": "tenant-b",
                "Content-Type": "application/json",
            },
        )
        self.assertEqual(response.status_code, 403)

    def test_risk_evaluation_rejects_invalid_payload(self) -> None:
        token = _service_principal_token("tenant-a")
        payload = _valid_payload()
        payload["snapshot"].pop("daily_pnl")

        response = self.client.post(
            self.path,
            json=payload,
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "invalid_snapshot")

    def test_risk_evaluation_returns_expected_shape(self) -> None:
        token = _service_principal_token("tenant-a")

        response = self.client.post(
            self.path,
            json=_valid_payload(),
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "evaluated")
        self.assertEqual(body["tenant_id"], "tenant-a")
        self.assertEqual(body["risk_status"], "active")
        self.assertEqual(body["trading_locked"], False)
        self.assertEqual(body["trading_day"], "2026-03-10")
        self.assertIn("loss_ratio", body)


if __name__ == "__main__":
    unittest.main()
