"""Normalization helpers for mapping platform-native snapshots into canonical models."""

from .models import CanonicalAccountSnapshot, PlatformAccountSnapshot


def derive_starting_balance(snapshot: PlatformAccountSnapshot):
    """Return starting balance and whether it was derived from available fields."""
    if snapshot.starting_balance is not None:
        return snapshot.starting_balance, False

    if snapshot.current_balance is None or snapshot.daily_pnl is None:
        return None, False

    return snapshot.current_balance - snapshot.daily_pnl, True


def normalize_account_snapshot(snapshot: PlatformAccountSnapshot) -> CanonicalAccountSnapshot:
    """Produce the canonical account snapshot while marking derived fields explicitly."""
    starting_balance, derived = derive_starting_balance(snapshot)
    derived_fields = ("starting_balance",) if derived else ()

    return CanonicalAccountSnapshot(
        source_platform=snapshot.platform_name,
        external_account_id=snapshot.external_account_id,
        current_balance=snapshot.current_balance,
        daily_pnl=snapshot.daily_pnl,
        starting_balance=starting_balance,
        derived_fields=derived_fields,
    )
