"""Persistence service contract for risk-state evaluations."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Mapping, Optional, Protocol

from app.ingestion.account_models import CanonicalAccountSnapshot


@dataclass(frozen=True)
class RiskStateSnapshot:
    """Canonical persisted representation for a risk-state evaluation."""

    tenant_id: str
    connector_id: str
    source_account_id: str
    event_ts: str
    trading_day: str
    risk_status: str
    trading_locked: bool
    loss_ratio: Optional[Decimal]


class RiskStateRepository(Protocol):
    """Storage contract for idempotent risk-state insertion."""

    def insert_state_if_new(self, state: RiskStateSnapshot) -> bool:
        """Return True when state is newly persisted, False when duplicate."""


class RiskStatePersistenceService:
    """Coordinates conversion and idempotent persistence of risk-state snapshots."""

    def __init__(self, repository: RiskStateRepository) -> None:
        self._repository = repository

    def persist_if_new(
        self,
        *,
        snapshot: CanonicalAccountSnapshot,
        evaluation: Mapping[str, object],
    ) -> bool:
        state = RiskStateSnapshot(
            tenant_id=snapshot.tenant_id,
            connector_id=snapshot.connector_id,
            source_account_id=snapshot.source_account_id,
            event_ts=snapshot.event_ts,
            trading_day=str(evaluation["trading_day"]),
            risk_status=str(evaluation["status"]),
            trading_locked=bool(evaluation["trading_locked"]),
            loss_ratio=_to_optional_decimal(evaluation.get("loss_ratio")),
        )
        return self._repository.insert_state_if_new(state)


def _to_optional_decimal(value: object) -> Optional[Decimal]:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))

