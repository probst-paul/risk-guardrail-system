"""FastAPI entrypoint for the Risk Guardrail backend service."""

from fastapi import FastAPI

app = FastAPI(
    title="Risk Guardrail API",
    version="0.1.0",
    description="Sprint 0 scaffold for the Risk Guardrail System backend.",
)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    """Health probe used by local orchestration and service checks."""
    return {"status": "ok", "service": "api"}
