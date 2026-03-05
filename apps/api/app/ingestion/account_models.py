"""Canonical account snapshot model and payload validation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping, Optional


class CanonicalAccountValidationError(ValueError):
    """Raised when account snapshot payload validation fails."""


@dataclass(frozen=True)
class CanonicalAccountSnapshot:
    tenant_id: str
    connector_id: str
    source_account_id: str
    event_ts: str
    current_balance: Decimal
    daily_pnl: Decimal
    account_currency: str
    trading_is_disabled: bool
    starting_balance: Optional[Decimal] = None
    daily_net_loss_limit: Optional[Decimal] = None


def canonical_account_snapshot_from_dict(
    payload: Mapping[str, Any],
) -> CanonicalAccountSnapshot:
    """Validate and convert input payload into canonical account snapshot."""
    tenant_id = _required_str(payload, "tenant_id")
    connector_id = _required_str(payload, "connector_id")
    source_account_id = _required_str(payload, "source_account_id")
    event_ts = _required_iso_timestamp(payload, "event_ts")
    current_balance = _required_decimal(payload, "current_balance", strictly_positive=True)
    daily_pnl = _required_decimal(payload, "daily_pnl", strictly_positive=False)
    account_currency = _required_str(payload, "account_currency")
    trading_is_disabled = _required_bool(payload, "trading_is_disabled")
    starting_balance = _optional_decimal(payload, "starting_balance")
    daily_net_loss_limit = _optional_decimal(payload, "daily_net_loss_limit")

    return CanonicalAccountSnapshot(
        tenant_id=tenant_id,
        connector_id=connector_id,
        source_account_id=source_account_id,
        event_ts=event_ts,
        current_balance=current_balance,
        daily_pnl=daily_pnl,
        account_currency=account_currency,
        trading_is_disabled=trading_is_disabled,
        starting_balance=starting_balance,
        daily_net_loss_limit=daily_net_loss_limit,
    )


def _required_str(payload: Mapping[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value:
        raise CanonicalAccountValidationError(f"missing or invalid field: {key}")
    return value


def _required_bool(payload: Mapping[str, Any], key: str) -> bool:
    value = payload.get(key)
    if not isinstance(value, bool):
        raise CanonicalAccountValidationError(f"missing or invalid field: {key}")
    return value


def _required_decimal(
    payload: Mapping[str, Any], key: str, *, strictly_positive: bool
) -> Decimal:
    value = payload.get(key)
    try:
        decimal_value = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise CanonicalAccountValidationError(f"missing or invalid field: {key}") from None

    if strictly_positive and decimal_value <= 0:
        raise CanonicalAccountValidationError(f"field must be > 0: {key}")

    return decimal_value


def _optional_decimal(payload: Mapping[str, Any], key: str) -> Optional[Decimal]:
    if key not in payload or payload.get(key) is None:
        return None

    value = payload.get(key)
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise CanonicalAccountValidationError(f"invalid optional field: {key}") from None


def _required_iso_timestamp(payload: Mapping[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value:
        raise CanonicalAccountValidationError(f"missing or invalid field: {key}")

    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        raise CanonicalAccountValidationError(f"invalid timestamp field: {key}") from None

    if parsed.tzinfo is None:
        raise CanonicalAccountValidationError(f"timestamp must include timezone: {key}")

    return parsed.astimezone(timezone.utc).isoformat()

