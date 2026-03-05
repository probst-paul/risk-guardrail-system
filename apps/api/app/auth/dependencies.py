"""FastAPI dependencies for authentication, tenancy, and authorization."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from fastapi import Header, HTTPException, status

from .config import get_expected_audience, get_expected_issuer
from .guard import AuthorizationError, require_roles, resolve_effective_tenant
from .identity import IdentityError, RequestIdentity, identity_from_claims
from .jwt import JwtValidationError, decode_unverified_claims, validate_registered_claims

@dataclass(frozen=True)
class AuthenticatedRequest:
    identity: RequestIdentity
    effective_tenant_id: str


def authenticate_request(
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
    x_tenant_id: Optional[str] = Header(default=None, alias="X-Tenant-Id"),
) -> AuthenticatedRequest:
    """Authenticate request and resolve effective tenant scope."""
    try:
        identity = _resolve_authenticated_identity(authorization)
        effective_tenant_id = resolve_effective_tenant(identity, requested_tenant_id=x_tenant_id)
    except AuthorizationError:
        _raise_forbidden()

    return AuthenticatedRequest(identity=identity, effective_tenant_id=effective_tenant_id)


def enforce_required_roles(
    auth: AuthenticatedRequest, *, required_roles: list[str]
) -> None:
    """Raise HTTP 403 when required roles are not satisfied."""
    try:
        require_roles(auth.identity, required_roles=required_roles)
    except AuthorizationError:
        _raise_forbidden()


def _resolve_authenticated_identity(authorization: Optional[str]) -> RequestIdentity:
    token = _extract_bearer_token(authorization)
    claims = _decode_and_validate_claims(token)
    try:
        return identity_from_claims(claims)
    except IdentityError:
        _raise_invalid_token()
    raise RuntimeError("unreachable")


def _decode_and_validate_claims(token: str) -> dict:
    try:
        claims = decode_unverified_claims(token)
        validate_registered_claims(
            claims,
            expected_issuer=get_expected_issuer(),
            expected_audience=get_expected_audience(),
            now=datetime.now(timezone.utc),
        )
    except JwtValidationError:
        _raise_invalid_token()
    return dict(claims)


def _extract_bearer_token(authorization: Optional[str]) -> str:
    if not authorization:
        _raise_unauthorized("missing_authorization")

    prefix = "Bearer "
    if not authorization.startswith(prefix):
        _raise_unauthorized("invalid_authorization")

    token = authorization[len(prefix) :].strip()
    if not token:
        _raise_unauthorized("invalid_authorization")

    return token


def _raise_invalid_token() -> None:
    _raise_unauthorized("invalid_token")


def _raise_unauthorized(detail: str) -> None:
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


def _raise_forbidden() -> None:
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")
