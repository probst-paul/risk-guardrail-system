"""FastAPI entrypoint for the Risk Guardrail backend service."""

import os
from typing import Dict, Union

from fastapi import Depends, FastAPI, HTTPException, status

from app.auth.dependencies import (
    AuthenticatedRequest,
    authenticate_request,
    enforce_required_roles,
)
from app.auth.guard import AuthorizationError, enforce_tenant_scope
from app.ingestion.account_models import (
    CanonicalAccountValidationError,
    canonical_account_snapshot_from_dict,
)
from app.ingestion.persistence import AccountSnapshotPersistenceService
from app.ingestion.postgres_repository import PostgresAccountSnapshotRepository
from app.risk.persistence import RiskStatePersistenceService
from app.risk.postgres_repository import PostgresRiskStateRepository
from app.risk.state_machine import evaluate_daily_risk_state

app = FastAPI(
    title="Risk Guardrail API",
    version="0.1.0",
    description="Sprint 0 scaffold for the Risk Guardrail System backend.",
)

class PersistenceUnavailableError(RuntimeError):
    """Raised when snapshot persistence cannot acquire a usable DB dependency."""


def get_db_connection():
    """Return a PostgreSQL connection when runtime configuration supports it."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        return None

    try:
        import psycopg  # type: ignore
    except Exception:  # noqa: BLE001
        return None

    try:
        return psycopg.connect(database_url)
    except Exception:  # noqa: BLE001
        return None


def _build_snapshot_persistence_service() -> AccountSnapshotPersistenceService:
    connection = get_db_connection()
    if connection and hasattr(connection, "cursor") and hasattr(connection, "commit"):
        on_close = connection.close if hasattr(connection, "close") else None
        return AccountSnapshotPersistenceService(
            PostgresAccountSnapshotRepository(connection),
            on_close=on_close,
        )
    if connection and hasattr(connection, "close"):
        try:
            connection.close()
        except Exception:  # noqa: BLE001
            pass
    raise PersistenceUnavailableError("persistence_unavailable")


def _build_risk_persistence_services() -> tuple[
    AccountSnapshotPersistenceService,
    RiskStatePersistenceService,
]:
    connection = get_db_connection()
    if connection and hasattr(connection, "cursor") and hasattr(connection, "commit"):
        return (
            AccountSnapshotPersistenceService(
                PostgresAccountSnapshotRepository(connection),
                on_close=connection.close if hasattr(connection, "close") else None,
            ),
            RiskStatePersistenceService(PostgresRiskStateRepository(connection)),
        )
    if connection and hasattr(connection, "close"):
        try:
            connection.close()
        except Exception:  # noqa: BLE001
            pass
    raise PersistenceUnavailableError("persistence_unavailable")


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    """Health probe used by local orchestration and service checks."""
    return {"status": "ok", "service": "api"}


@app.post("/v1/admin/accounts/{account_id}/unlock", tags=["admin"])
def unlock_account(
    account_id: str, auth: AuthenticatedRequest = Depends(authenticate_request)
) -> dict[str, str]:
    """Admin placeholder endpoint with role-based authorization guard."""
    enforce_required_roles(auth, required_roles=["risk_admin"])
    return {
        "status": "accepted",
        "account_id": account_id,
        "tenant_id": auth.effective_tenant_id,
    }


@app.post("/v1/fills:ingest", tags=["ingestion"])
def ingest_fills(
    auth: AuthenticatedRequest = Depends(authenticate_request),
) -> dict[str, str]:
    """Ingestion placeholder endpoint with authenticated tenant scope."""
    return {"status": "accepted", "tenant_id": auth.effective_tenant_id}


@app.post("/v1/accounts:snapshot", tags=["ingestion"])
def ingest_account_snapshots(
    payload: dict,
    auth: AuthenticatedRequest = Depends(authenticate_request),
) -> Dict[str, Union[str, int]]:
    """Account snapshot ingestion placeholder with auth and tenant guardrails."""
    enforce_required_roles(auth, required_roles=["service_principal"])

    snapshots = payload.get("snapshots")
    if not isinstance(snapshots, list) or not snapshots:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="invalid_payload",
        )

    canonical_snapshots = []
    for raw_snapshot in snapshots:
        if not isinstance(raw_snapshot, dict):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="invalid_payload",
            )
        try:
            snapshot = canonical_account_snapshot_from_dict(raw_snapshot)
            enforce_tenant_scope(auth.identity, resource_tenant_id=snapshot.tenant_id)
        except CanonicalAccountValidationError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="invalid_snapshot",
            ) from None
        except AuthorizationError:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="forbidden",
            ) from None
        canonical_snapshots.append(snapshot)

    try:
        persistence_service = _build_snapshot_persistence_service()
    except PersistenceUnavailableError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="persistence_unavailable",
        ) from None
    try:
        persistence_result = persistence_service.persist_batch(canonical_snapshots)
    finally:
        persistence_service.close()

    return {
        "status": "accepted",
        "tenant_id": auth.effective_tenant_id,
        "accepted_count": persistence_result.total_count,
        "total_count": persistence_result.total_count,
        "persisted_count": persistence_result.persisted_count,
        "duplicate_count": persistence_result.duplicate_count,
    }


@app.post("/v1/risk:evaluate", tags=["ingestion"])
def evaluate_risk(
    payload: dict,
    auth: AuthenticatedRequest = Depends(authenticate_request),
) -> Dict[str, Union[str, int, bool, None, float]]:
    """Evaluate account risk state from a canonical snapshot payload."""
    enforce_required_roles(auth, required_roles=["service_principal"])

    raw_snapshot = payload.get("snapshot")
    if not isinstance(raw_snapshot, dict):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="invalid_payload",
        )

    try:
        snapshot = canonical_account_snapshot_from_dict(raw_snapshot)
        enforce_tenant_scope(auth.identity, resource_tenant_id=snapshot.tenant_id)
    except CanonicalAccountValidationError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="invalid_snapshot",
        ) from None
    except AuthorizationError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="forbidden",
        ) from None

    evaluation = evaluate_daily_risk_state(snapshot)

    # Risk-state persistence is best-effort in this slice so API evaluation remains available
    # outside full DB-backed environments.
    try:
        snapshot_service, risk_service = _build_risk_persistence_services()
        try:
            snapshot_service.persist_batch([snapshot])
            risk_service.persist_if_new(snapshot=snapshot, evaluation=evaluation)
        finally:
            snapshot_service.close()
    except PersistenceUnavailableError:
        pass
    except Exception:  # noqa: BLE001
        # Risk evaluation remains available even when persistence linkage fails.
        pass

    loss_ratio = evaluation.get("loss_ratio")
    serialized_loss_ratio = float(loss_ratio) if loss_ratio is not None else None

    return {
        "status": "evaluated",
        "tenant_id": auth.effective_tenant_id,
        "risk_status": str(evaluation["status"]),
        "trading_locked": bool(evaluation["trading_locked"]),
        "trading_day": str(evaluation["trading_day"]),
        "loss_ratio": serialized_loss_ratio,
    }
