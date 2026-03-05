import unittest

from app.auth.guard import (
    AuthorizationError,
    enforce_tenant_scope,
    require_roles,
    resolve_effective_tenant,
)
from app.auth.identity import RequestIdentity


class TenantGuardContractTest(unittest.TestCase):
    def test_resolve_effective_tenant_uses_identity_tenant_by_default(self) -> None:
        identity = RequestIdentity(
            subject="user-1",
            tenant_id="tenant-a",
            roles=frozenset({"viewer"}),
            principal_type="user",
        )

        effective_tenant = resolve_effective_tenant(identity, requested_tenant_id=None)

        self.assertEqual(effective_tenant, "tenant-a")

    def test_resolve_effective_tenant_rejects_cross_tenant_request(self) -> None:
        identity = RequestIdentity(
            subject="user-1",
            tenant_id="tenant-a",
            roles=frozenset({"viewer"}),
            principal_type="user",
        )

        with self.assertRaises(AuthorizationError):
            resolve_effective_tenant(identity, requested_tenant_id="tenant-b")

    def test_enforce_tenant_scope_allows_matching_tenant(self) -> None:
        identity = RequestIdentity(
            subject="user-1",
            tenant_id="tenant-a",
            roles=frozenset({"risk_admin"}),
            principal_type="user",
        )

        enforce_tenant_scope(identity, resource_tenant_id="tenant-a")

    def test_enforce_tenant_scope_rejects_mismatched_tenant(self) -> None:
        identity = RequestIdentity(
            subject="user-1",
            tenant_id="tenant-a",
            roles=frozenset({"risk_admin"}),
            principal_type="user",
        )

        with self.assertRaises(AuthorizationError):
            enforce_tenant_scope(identity, resource_tenant_id="tenant-b")

    def test_require_roles_allows_risk_admin_for_admin_action(self) -> None:
        identity = RequestIdentity(
            subject="user-1",
            tenant_id="tenant-a",
            roles=frozenset({"risk_admin"}),
            principal_type="user",
        )

        require_roles(identity, required_roles=["risk_admin"])

    def test_require_roles_denies_without_matching_role(self) -> None:
        identity = RequestIdentity(
            subject="user-1",
            tenant_id="tenant-a",
            roles=frozenset({"viewer"}),
            principal_type="user",
        )

        with self.assertRaises(AuthorizationError):
            require_roles(identity, required_roles=["risk_admin"])

    def test_require_roles_is_deny_by_default_when_roles_not_declared(self) -> None:
        identity = RequestIdentity(
            subject="user-1",
            tenant_id="tenant-a",
            roles=frozenset({"risk_admin"}),
            principal_type="user",
        )

        with self.assertRaises(AuthorizationError):
            require_roles(identity, required_roles=[])


if __name__ == "__main__":
    unittest.main()
