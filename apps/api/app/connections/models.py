from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any


@dataclass(frozen=True)
class PlatformCapabilities:
    has_starting_balance: bool = False
    has_daily_pnl: bool = False
    supports_cursor_paging: bool = False
    requires_polling: bool = True


@dataclass(frozen=True)
class PlatformAccountSnapshot:
    platform_name: str
    external_account_id: str
    current_balance: Decimal | None = None
    daily_pnl: Decimal | None = None
    starting_balance: Decimal | None = None
    raw_payload: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CanonicalAccountSnapshot:
    source_platform: str
    external_account_id: str
    current_balance: Decimal | None
    daily_pnl: Decimal | None
    starting_balance: Decimal | None
    derived_fields: tuple[str, ...] = ()
