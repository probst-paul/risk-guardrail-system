import unittest
from decimal import Decimal

from app.connections.models import PlatformAccountSnapshot
from app.connections.normalization import normalize_account_snapshot


class ConnectionNormalizationTest(unittest.TestCase):
    def test_derives_starting_balance_when_missing(self) -> None:
        snapshot = PlatformAccountSnapshot(
            platform_name="rithmic",
            external_account_id="acct-123",
            current_balance=Decimal("103500.25"),
            daily_pnl=Decimal("350.25"),
        )

        canonical = normalize_account_snapshot(snapshot)

        self.assertEqual(canonical.starting_balance, Decimal("103150.00"))
        self.assertEqual(canonical.derived_fields, ("starting_balance",))

    def test_preserves_native_starting_balance_when_present(self) -> None:
        snapshot = PlatformAccountSnapshot(
            platform_name="sierra_chart",
            external_account_id="acct-456",
            current_balance=Decimal("100500.00"),
            daily_pnl=Decimal("500.00"),
            starting_balance=Decimal("100000.00"),
        )

        canonical = normalize_account_snapshot(snapshot)

        self.assertEqual(canonical.starting_balance, Decimal("100000.00"))
        self.assertEqual(canonical.derived_fields, ())


if __name__ == "__main__":
    unittest.main()
