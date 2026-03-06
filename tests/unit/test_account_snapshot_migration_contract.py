import re
import unittest
from pathlib import Path


MIGRATIONS_DIR = (
    Path(__file__).resolve().parents[2]
    / "apps"
    / "api"
    / "migrations"
    / "versions"
)


class AccountSnapshotMigrationContractTest(unittest.TestCase):
    def _find_account_snapshot_migration(self) -> Path:
        candidates = sorted(
            path for path in MIGRATIONS_DIR.glob("*.py") if "account_snapshot" in path.name
        )
        self.assertTrue(
            candidates,
            "Expected an account snapshot migration file in apps/api/migrations/versions/",
        )
        return candidates[-1]

    def test_migration_exists_for_account_snapshot_table(self) -> None:
        migration_path = self._find_account_snapshot_migration()
        source = migration_path.read_text()

        self.assertIn('op.create_table(\n        "account_snapshots"', source)

    def test_migration_declares_idempotency_uniqueness_key(self) -> None:
        migration_path = self._find_account_snapshot_migration()
        source = migration_path.read_text()

        self.assertRegex(
            source,
            re.compile(
                r'name="uq_account_snapshots_idempotency".*tenant_id.*connector_id.*source_account_id.*event_ts',
                re.S,
            ),
        )

    def test_migration_declares_tenant_and_lookup_indexes(self) -> None:
        migration_path = self._find_account_snapshot_migration()
        source = migration_path.read_text()

        self.assertIn('"ix_account_snapshots_tenant_id"', source)
        self.assertIn('"ix_account_snapshots_connector_account"', source)


if __name__ == "__main__":
    unittest.main()
