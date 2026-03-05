# Risk Guardrail System

Risk Guardrail System is a multi-tenant risk control plane for trading-style event streams. This repository starts with a backend-first Sprint 0 scaffold: a monorepo baseline, contract-first backend API definition, local Compose topology, and an initial docs pack.

## Scope of the first commit

This scaffold covers the project plan's Sprint 0 goals:

- Repository skeleton for the backend API, contracts, tests, and docs
- `docker-compose.yml` baseline for local development
- OpenAPI contract-of-record baseline under `openapi/`
- Lightweight contract test harness
- Initial documentation pack and first ADR

This commit does not implement tenancy, auth, ingestion, risk evaluation, or persistence yet. Those belong to later sprints.

## Repository layout

```text
.
├── apps/
│   ├── api/
│   │   ├── app/
│   │   │   └── connections/
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
│   └── contracts/
│       └── test_openapi_baseline.py
├── .env.example
├── .gitignore
├── Makefile
└── docker-compose.yml
```

## Planned architecture

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

### Service stubs

```bash
docker compose up --build
```

Expected endpoints after the scaffold:

- API health: `http://localhost:8000/health`
- PostgreSQL: `localhost:5432`

### Development notes

- Use `.env.example` as the local starting point for environment variables.
- `make test` runs the contract and unit test suites.
- `make db-upgrade` applies the latest API schema migration set.
- The API Docker build excludes local caches and test artifacts via `apps/api/.dockerignore`.

## Roadmap

Implementation sequencing lives in [docs/roadmap.md](docs/roadmap.md).

## Current decisions

- Monorepo layout to keep the backend app plus shared contracts and docs versioned together
- OpenAPI checked in as the contract of record for the backend API before endpoint implementation expands
- Service stubs are intentionally minimal to avoid pretending the system exists before the tenancy and data model work lands
