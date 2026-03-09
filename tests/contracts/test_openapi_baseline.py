import json
import unittest
from pathlib import Path


SPEC_PATH = Path(__file__).resolve().parents[2] / "openapi" / "risk-guardrail.v1.json"


class OpenApiBaselineTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.spec = json.loads(SPEC_PATH.read_text())

    def test_uses_openapi_31(self) -> None:
        self.assertEqual(self.spec["openapi"], "3.1.0")

    def test_has_core_paths(self) -> None:
        paths = self.spec["paths"]
        self.assertIn("/health", paths)
        self.assertIn("/v1/fills:ingest", paths)
        self.assertIn("/v1/accounts:snapshot", paths)
        self.assertIn("/v1/risk:evaluate", paths)
        self.assertIn("/v1/admin/accounts/{accountId}/unlock", paths)

    def test_health_response_schema_is_present(self) -> None:
        schema = self.spec["components"]["schemas"]["HealthResponse"]
        self.assertEqual(schema["type"], "object")
        self.assertEqual(schema["required"], ["status", "service"])

    def test_contract_tracks_system_ingestion_and_admin_tags(self) -> None:
        tag_names = {tag["name"] for tag in self.spec["tags"]}
        self.assertTrue({"system", "ingestion", "admin"}.issubset(tag_names))

    def test_bearer_security_scheme_is_declared(self) -> None:
        schemes = self.spec["components"]["securitySchemes"]
        self.assertIn("bearerAuth", schemes)
        self.assertEqual(schemes["bearerAuth"]["type"], "http")
        self.assertEqual(schemes["bearerAuth"]["scheme"], "bearer")

    def test_protected_paths_require_bearer_auth(self) -> None:
        ingest_security = self.spec["paths"]["/v1/fills:ingest"]["post"]["security"]
        snapshot_security = self.spec["paths"]["/v1/accounts:snapshot"]["post"]["security"]
        risk_security = self.spec["paths"]["/v1/risk:evaluate"]["post"]["security"]
        unlock_security = self.spec["paths"]["/v1/admin/accounts/{accountId}/unlock"]["post"][
            "security"
        ]
        self.assertEqual(ingest_security, [{"bearerAuth": []}])
        self.assertEqual(snapshot_security, [{"bearerAuth": []}])
        self.assertEqual(risk_security, [{"bearerAuth": []}])
        self.assertEqual(unlock_security, [{"bearerAuth": []}])

    def test_account_snapshot_ingest_response_schema_is_present(self) -> None:
        schema = self.spec["components"]["schemas"]["AccountSnapshotIngestResponse"]
        self.assertEqual(schema["type"], "object")
        self.assertEqual(
            schema["required"],
            [
                "status",
                "tenant_id",
                "accepted_count",
                "total_count",
                "persisted_count",
                "duplicate_count",
            ],
        )

    def test_account_snapshot_ingest_declares_persistence_unavailable_response(self) -> None:
        responses = self.spec["paths"]["/v1/accounts:snapshot"]["post"]["responses"]
        self.assertIn("503", responses)
        self.assertIn("persistence", responses["503"]["description"].lower())

    def test_risk_evaluation_response_schema_is_present(self) -> None:
        schema = self.spec["components"]["schemas"]["RiskEvaluationResponse"]
        self.assertEqual(schema["type"], "object")
        self.assertEqual(
            schema["required"],
            [
                "status",
                "tenant_id",
                "risk_status",
                "trading_locked",
                "trading_day",
                "loss_ratio",
            ],
        )


if __name__ == "__main__":
    unittest.main()
