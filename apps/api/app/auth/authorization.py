"""Authorization primitives with deny-by-default behavior."""

from __future__ import annotations

from collections.abc import Iterable

from .identity import RequestIdentity


def is_authorized(identity: RequestIdentity, required_roles: Iterable[str]) -> bool:
    """Return True only when at least one required role is present."""
    required = {role for role in required_roles if role}
    if not required:
        return False
    return any(role in identity.roles for role in required)

