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
        unlock_security = self.spec["paths"]["/v1/admin/accounts/{accountId}/unlock"]["post"][
            "security"
        ]
        self.assertEqual(ingest_security, [{"bearerAuth": []}])
        self.assertEqual(unlock_security, [{"bearerAuth": []}])


if __name__ == "__main__":
    unittest.main()
