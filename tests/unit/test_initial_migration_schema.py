import unittest
from pathlib import Path


MIGRATION_PATH = (
    Path(__file__).resolve().parents[2]
    / "apps"
    / "api"
    / "migrations"
    / "versions"
    / "20260305_0001_initial_tenancy_schema.py"
)


class InitialMigrationSchemaTest(unittest.TestCase):
    def test_migration_declares_expected_tables_and_constraints(self) -> None:
        source = MIGRATION_PATH.read_text()

        self.assertIn("CREATE EXTENSION IF NOT EXISTS pgcrypto", source)
        self.assertIn('op.create_table(\n        "tenants"', source)
        self.assertIn('op.create_table(\n        "users"', source)
        self.assertIn('op.create_table(\n        "service_principals"', source)

        self.assertIn('name="uq_tenants_slug"', source)
        self.assertIn('name="ck_tenants_status"', source)
        self.assertIn('name="uq_users_tenant_subject"', source)
        self.assertIn('name="ck_users_role"', source)
        self.assertIn('name="uq_service_principals_client_id"', source)
        self.assertIn('name="uq_service_principals_tenant_name"', source)
        self.assertIn('name="ck_service_principals_role"', source)
        self.assertIn('"ix_users_tenant_id"', source)
        self.assertIn('"ix_service_principals_tenant_id"', source)


if __name__ == "__main__":
    unittest.main()
