"""Tenant guard and role enforcement primitives."""

from __future__ import annotations

from collections.abc import Iterable

from .authorization import is_authorized
from .identity import RequestIdentity


class AuthorizationError(PermissionError):
    """Raised when a request is not authorized for the attempted operation."""


def resolve_effective_tenant(
    identity: RequestIdentity, *, requested_tenant_id: str | None
) -> str:
    """Resolve the effective tenant and reject cross-tenant overrides."""
    if not requested_tenant_id:
        return identity.tenant_id

    if requested_tenant_id != identity.tenant_id:
        raise AuthorizationError("cross-tenant access denied")

    return requested_tenant_id


def enforce_tenant_scope(identity: RequestIdentity, *, resource_tenant_id: str) -> None:
    """Ensure the identity is scoped to the same tenant as the resource."""
    if resource_tenant_id != identity.tenant_id:
        raise AuthorizationError("tenant scope mismatch")


def require_roles(identity: RequestIdentity, *, required_roles: Iterable[str]) -> None:
    """Deny by default unless one required role is present."""
    if not is_authorized(identity, required_roles):
        raise AuthorizationError("role requirement not satisfied")

