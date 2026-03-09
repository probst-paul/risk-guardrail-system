"""Risk-state transition logic for account-level daily guardrails."""

from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Mapping, Optional
from zoneinfo import ZoneInfo

from app.ingestion.account_models import CanonicalAccountSnapshot


WARNING_THRESHOLD = Decimal("0.8")
DEFAULT_SESSION_TIMEZONE = "America/Chicago"
DEFAULT_SESSION_START_TIME = "17:00"


def evaluate_daily_risk_state(
    snapshot: CanonicalAccountSnapshot,
    *,
    previous_state: Optional[Mapping[str, object]] = None,
    session_policy: Optional[Mapping[str, str]] = None,
) -> dict[str, object]:
    """Evaluate current risk status from a canonical snapshot and prior state."""
    trading_day = _trading_day(snapshot.event_ts, session_policy=session_policy)
    loss_ratio = _loss_ratio(snapshot)

    if _is_sticky_breach(previous_state, trading_day=trading_day):
        return {
            "status": "breached",
            "loss_ratio": loss_ratio,
            "trading_locked": True,
            "trading_day": trading_day,
        }

    status = _status_from_ratio(loss_ratio)
    return {
        "status": status,
        "loss_ratio": loss_ratio,
        "trading_locked": status == "breached",
        "trading_day": trading_day,
    }


def _loss_ratio(snapshot: CanonicalAccountSnapshot) -> Optional[Decimal]:
    limit = snapshot.daily_net_loss_limit
    if limit is None or limit <= 0:
        return None

    daily_loss = abs(min(snapshot.daily_pnl, Decimal("0")))
    return daily_loss / limit


def _status_from_ratio(loss_ratio: Optional[Decimal]) -> str:
    if loss_ratio is None:
        return "active"
    if loss_ratio >= Decimal("1"):
        return "breached"
    if loss_ratio >= WARNING_THRESHOLD:
        return "warning"
    return "active"


def _is_sticky_breach(
    previous_state: Optional[Mapping[str, object]], *, trading_day: str
) -> bool:
    if previous_state is None:
        return False
    return (
        previous_state.get("status") == "breached"
        and previous_state.get("trading_day") == trading_day
    )


def _trading_day(event_ts: str, *, session_policy: Optional[Mapping[str, str]]) -> str:
    policy = session_policy or {}
    timezone_name = policy.get("timezone", DEFAULT_SESSION_TIMEZONE)
    session_start_time = policy.get("session_start_time", DEFAULT_SESSION_START_TIME)

    local_dt = datetime.fromisoformat(event_ts).astimezone(ZoneInfo(timezone_name))
    session_hour, session_minute = _parse_session_time(session_start_time)

    if (local_dt.hour, local_dt.minute) >= (session_hour, session_minute):
        return (local_dt.date() + timedelta(days=1)).isoformat()
    return local_dt.date().isoformat()


def _parse_session_time(value: str) -> tuple[int, int]:
    hour_str, minute_str = value.split(":", maxsplit=1)
    return int(hour_str), int(minute_str)
