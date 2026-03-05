# Roadmap

This document keeps implementation sequencing separate from the durable technical docs.

## Planned phases

1. Foundations
   Repository skeleton, local Compose baseline, OpenAPI contract baseline, contract-test harness, and docs scaffolding.
2. Tenancy-first schema and auth
   Schema and migrations for tenants, users, and service principals, plus JWT validation, tenant guard, and deny-by-default authorization.
3. Canonical model and ingestion API
   Canonical fill model, ingestion endpoints, idempotent persistence, dedupe constraints, and transaction-focused tests.
4. Risk engine and state machine
   Daily risk state transitions, threshold logic, invariants, and metrics.
5. Audit logging and admin actions
   Append-only audit log, reason-required administrative actions, and RBAC verification.
6. Platform emulator
   Standalone broker-like simulator app with deterministic scenarios and platform-style endpoints for safe demos and connector development.
7. Connector service
   Polling, checkpointing, transformation, retry behavior, and no-double-apply guarantees against external platforms.
8. Reporting and web admin MVP
   Reporting endpoints, audit views, operator workflows, and a minimal web admin experience.
9. Hardening and documentation pack
   Threat model, operations guidance, ADRs, observability polish, and load-test smoke coverage.
10. Optional Spring Boot proof-of-parity slice
   One vertical slice reimplemented in Spring Boot under the same contract and validated for parity.

## Portfolio context

This roadmap documents implementation order and scope boundaries from initial scaffold through production-oriented backend capabilities.
