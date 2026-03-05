# ADR 0001: Monorepo Scaffold and Contract-First Baseline

## Status

Accepted

## Context

The project needs multiple deployable units:

- a FastAPI backend API
- shared HTTP contracts and documentation

The first commit should optimize for coordinated evolution across those units while preserving explicit boundaries.

## Decision

Use a monorepo with an application directory under `apps/`, a checked-in OpenAPI contract under `openapi/` for the backend API, and documentation under `docs/`.

## Consequences

- API, tests, and docs evolve together in a single review surface
- Contract drift is easier to catch early
- Future extraction into separate deployment artifacts remains straightforward because boundaries are explicit
