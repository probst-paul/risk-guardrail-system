"""FastAPI entrypoint for the Risk Guardrail backend service."""

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
from app.ingestion.persistence import (
    AccountSnapshotPersistenceService,
    InMemoryAccountSnapshotRepository,
)

app = FastAPI(
    title="Risk Guardrail API",
    version="0.1.0",
    description="Sprint 0 scaffold for the Risk Guardrail System backend.",
)

_account_snapshot_repository = InMemoryAccountSnapshotRepository()
_account_snapshot_persistence_service = AccountSnapshotPersistenceService(
    _account_snapshot_repository
)


def reset_account_snapshot_persistence_state() -> None:
    """Reset in-memory snapshot persistence state (test helper)."""
    _account_snapshot_repository.clear()


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

    persistence_result = _account_snapshot_persistence_service.persist_batch(
        canonical_snapshots
    )

    return {
        "status": "accepted",
        "tenant_id": auth.effective_tenant_id,
        "accepted_count": persistence_result.total_count,
        "total_count": persistence_result.total_count,
        "persisted_count": persistence_result.persisted_count,
        "duplicate_count": persistence_result.duplicate_count,
    }
