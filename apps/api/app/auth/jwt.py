"""JWT registered-claim validation helpers."""

from __future__ import annotations

import base64
import json
from datetime import datetime, timezone
from typing import Any, Mapping


class JwtValidationError(ValueError):
    """Raised when JWT claims fail baseline validation."""


def decode_unverified_claims(token: str) -> Mapping[str, Any]:
    """Decode JWT payload claims without signature verification.

    This is a scaffold parser for local auth wiring and tests; signature
    verification is introduced in later hardening commits.
    """
    parts = token.split(".")
    if len(parts) != 3:
        raise JwtValidationError("malformed token")

    payload_segment = parts[1]
    padding = "=" * ((4 - len(payload_segment) % 4) % 4)
    try:
        payload_bytes = base64.urlsafe_b64decode(payload_segment + padding)
        payload = json.loads(payload_bytes.decode("utf-8"))
    except Exception as exc:  # noqa: BLE001
        raise JwtValidationError("invalid token payload") from exc

    if not isinstance(payload, dict):
        raise JwtValidationError("token payload must be an object")

    return payload


def validate_registered_claims(
    claims: Mapping[str, Any],
    *,
    expected_issuer: str,
    expected_audience: str,
    now: datetime | None = None,
) -> None:
    """Validate issuer, audience, and token temporal bounds."""
    current_time = now or datetime.now(timezone.utc)

    issuer = _required_str(claims, "iss")
    if issuer != expected_issuer:
        raise JwtValidationError("issuer mismatch")

    if not _audience_matches(claims.get("aud"), expected_audience):
        raise JwtValidationError("audience mismatch")

    issued_at = _required_timestamp(claims, "iat")
    expires_at = _required_timestamp(claims, "exp")

    if issued_at > current_time:
        raise JwtValidationError("token issued in the future")
    if expires_at <= current_time:
        raise JwtValidationError("token expired")

    _required_str(claims, "sub")
    _required_str(claims, "tenant_id")


def _required_str(claims: Mapping[str, Any], key: str) -> str:
    value = claims.get(key)
    if not isinstance(value, str) or not value:
        raise JwtValidationError(f"missing or invalid claim: {key}")
    return value


def _required_timestamp(claims: Mapping[str, Any], key: str) -> datetime:
    value = claims.get(key)
    if not isinstance(value, (int, float)):
        raise JwtValidationError(f"missing or invalid timestamp claim: {key}")
    return datetime.fromtimestamp(value, tz=timezone.utc)


def _audience_matches(aud_claim: Any, expected_audience: str) -> bool:
    if isinstance(aud_claim, str):
        return aud_claim == expected_audience
    if isinstance(aud_claim, (list, tuple, set)):
        return expected_audience in aud_claim
    return False

