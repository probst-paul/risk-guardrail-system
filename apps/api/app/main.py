"""FastAPI entrypoint for the Risk Guardrail backend service."""

from fastapi import Depends, FastAPI

from app.auth.dependencies import (
    AuthenticatedRequest,
    authenticate_request,
    enforce_required_roles,
)

app = FastAPI(
    title="Risk Guardrail API",
    version="0.1.0",
    description="Sprint 0 scaffold for the Risk Guardrail System backend.",
)


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
