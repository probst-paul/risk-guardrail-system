# Operations

## Local development baseline

- Start local services with `docker compose up --build`
- Run contract checks with `make test-contracts`
- Run full test suite with `make test`
- Apply migrations with `make db-upgrade`

## Expected local services

- API on port `8000`
- PostgreSQL on port `55432`

## Current operational behavior notes

- `POST /v1/accounts:snapshot` fails fast with `503` when DB persistence is unavailable.
- `POST /v1/risk:evaluate` returns evaluated risk response even if risk-state DB linkage write fails (best-effort linkage in this slice).
- Default trading-session boundary for risk state is `America/Chicago` at `17:00`.

## Future runbook topics

- Connector lag and heartbeat troubleshooting
- Token rotation for service principals
- Unlock workflow audit procedures
- Reprocessing and replay safety rules
