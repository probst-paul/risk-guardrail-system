"""Request identity model and claim-to-identity mapping."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


class IdentityError(ValueError):
    """Raised when required identity claims are missing or malformed."""


@dataclass(frozen=True)
class RequestIdentity:
    """Normalized identity resolved from validated token claims."""

    subject: str
    tenant_id: str
    roles: frozenset[str]
    principal_type: str


def identity_from_claims(claims: Mapping[str, Any]) -> RequestIdentity:
    """Build a request identity from validated claims."""
    subject = _required_str(claims, "sub")
    tenant_id = _required_str(claims, "tenant_id")
    principal_type = _required_str(claims, "principal_type")

    roles_claim = claims.get("roles")
    if not isinstance(roles_claim, (list, tuple, set)):
        raise IdentityError("roles claim must be a list-like value")

    roles: set[str] = set()
    for role in roles_claim:
        if not isinstance(role, str) or not role:
            raise IdentityError("roles claim must contain non-empty strings")
        roles.add(role)

    return RequestIdentity(
        subject=subject,
        tenant_id=tenant_id,
        roles=frozenset(roles),
        principal_type=principal_type,
    )


def _required_str(claims: Mapping[str, Any], key: str) -> str:
    value = claims.get(key)
    if not isinstance(value, str) or not value:
        raise IdentityError(f"missing or invalid claim: {key}")
    return value

