"""Persistence service contract for idempotent account snapshot writes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Protocol

from .account_models import CanonicalAccountSnapshot


class AccountSnapshotRepository(Protocol):
    """Storage contract for idempotent snapshot insertion."""

    def insert_snapshot_if_new(self, snapshot: CanonicalAccountSnapshot) -> bool:
        """Return True when snapshot is newly persisted, False when duplicate."""


@dataclass(frozen=True)
class PersistenceResult:
    total_count: int
    persisted_count: int
    duplicate_count: int


class AccountSnapshotPersistenceService:
    """Batch persistence coordinator with duplicate-safe accounting."""

    def __init__(self, repository: AccountSnapshotRepository) -> None:
        self._repository = repository

    def persist_batch(
        self, snapshots: Iterable[CanonicalAccountSnapshot]
    ) -> PersistenceResult:
        persisted_count = 0
        duplicate_count = 0
        total_count = 0

        for snapshot in snapshots:
            total_count += 1
            if self._repository.insert_snapshot_if_new(snapshot):
                persisted_count += 1
            else:
                duplicate_count += 1

        return PersistenceResult(
            total_count=total_count,
            persisted_count=persisted_count,
            duplicate_count=duplicate_count,
        )

