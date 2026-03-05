# API App

This directory contains the FastAPI control-plane backend.

## Local workflow

- Run tests from the repo root with `make test`
- Start the local stack from the repo root with `docker compose up --build`
- Use the root `.env.example` as the baseline local environment

## Auth testing notes

- Protected endpoints currently require a bearer token and enforce tenant/role guards.
- Request-level security behavior is covered by:
  - `tests/unit/test_api_security_negative_contract.py`
  - `tests/unit/test_api_auth_regressions.py`
- JWT signature verification is intentionally deferred; claim validation and guard behavior are implemented in this sprint.

## Database migrations

- Apply latest migrations from repo root: `make db-upgrade`
- Roll back one migration from repo root: `make db-downgrade`
- View migration history from repo root: `make db-history`

Responsibilities:

- expose the versioned backend API
- own tenancy, authorization, ingestion, policy, audit, and reporting behavior
- define behavior that must conform to the checked-in OpenAPI contract under `openapi/`
- provide the connection boundary for platform-specific normalization into canonical backend models

Non-responsibilities:

- broker emulation
- connector polling

## Connection boundary

Platform-specific integration code belongs under `app/connections/`.

That layer is responsible for:

- modeling platform-native payloads
- normalizing external data into canonical backend models
- deriving fields that are missing but inferable

It is not the place for a simulator server. If a simulator is added later, it should be a separate app that the connection layer talks to like any other external platform.
