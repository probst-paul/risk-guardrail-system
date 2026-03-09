# Risk Guardrail System

Risk Guardrail System is a multi-tenant risk control plane for trading-style event streams.

## Current implemented scope

The repository now includes a working backend baseline for:

- JWT-based request auth and tenant/role guards
- Canonical account snapshot ingestion with idempotent persistence semantics
- Risk evaluation state machine (`active`, `warning`, `breached`) with trading-session day boundaries
- Risk evaluation API endpoint and risk-state persistence linkage
- Migration-managed PostgreSQL schema for tenancy, snapshot ingestion, and risk-state snapshots
- Contract + unit + regression test coverage

## Repository layout

```text
.
├── apps/
│   ├── api/
│   │   ├── app/
│   │   │   ├── connections/
│   │   │   ├── ingestion/
│   │   │   ├── auth/
│   │   │   └── risk/
│   │   ├── migrations/
│   │   │   └── versions/
│   │   ├── alembic.ini
│   │   ├── Dockerfile
│   │   ├── README.md
│   │   └── pyproject.toml
├── docs/
│   ├── ADRs/
│   ├── OPERATIONS.md
│   ├── THREAT_MODEL.md
│   ├── architecture.md
│   ├── platform_contract.md
│   ├── roadmap.md
│   ├── security_model.md
│   └── testing_strategy.md
├── openapi/
│   └── risk-guardrail.v1.json
├── scripts/
│   └── check_openapi.py
├── tests/
│   ├── contracts/
│   └── unit/
├── .env.example
├── .gitignore
├── Makefile
└── docker-compose.yml
```

## Architecture

- `apps/api`: FastAPI backend API, the system-of-record boundary for tenancy, ingestion, policy evaluation, and reporting
- `apps/api/app/connections`: platform adapter boundary for Sierra Chart, Rithmic, NinjaTrader, simulator, or other external integrations
- `openapi/`: versioned HTTP contract for the backend API only
- `docs/platform_contract.md`: the external trading-platform contract that connectors normalize into canonical backend models
- `tests/contracts`: contract guardrails that fail when the baseline spec drifts in unsafe ways
- `docs/`: architecture, security, testing, operations, and ADR history

## Quick start

### Local checks

```bash
cp .env.example .env
make test
make db-upgrade
```

### Local services

```bash
docker compose up --build
```

Expected local endpoints:

- API health: `http://localhost:8000/health`
- Snapshot ingest: `http://localhost:8000/v1/accounts:snapshot`
- Risk evaluate: `http://localhost:8000/v1/risk:evaluate`
- PostgreSQL: `localhost:55432`

### Development notes

- Use `.env.example` as the local starting point for environment variables.
- `make test` runs the contract and unit test suites.
- `make db-upgrade` applies the latest API schema migration set.
- The API Docker build excludes local caches and test artifacts via `apps/api/.dockerignore`.

## Roadmap

Implementation sequencing lives in [docs/roadmap.md](docs/roadmap.md).

## Current decisions

- Monorepo layout to keep the backend app plus shared contracts and docs versioned together
- OpenAPI checked in as the contract of record for backend endpoint behavior
- TDD and contract-first sequencing for API and persistence slices
