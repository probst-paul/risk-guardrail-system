# Architecture

## Intent

The system is a multi-tenant risk control plane for trading-style event streams.

Initial component boundaries:

- `apps/api`: control-plane API for ingestion, policy management, risk state transitions, and reporting
- `apps/api/app/connections`: platform adapter boundary for external-platform normalization and capability handling
- `postgres`: system of record for tenant-scoped operational data

## Primary data flow

1. A future connector service polls external platform endpoints and converts platform-native payloads into canonical events.
2. The backend API ingests canonical events, persists immutable records, and computes derived risk state.
3. Operators use future admin/reporting endpoints and the eventual Web Admin to inspect and act on tenant-scoped state.

## Early constraints

- OpenAPI is the HTTP contract of record.
- The external trading-platform boundary is defined separately in `docs/platform_contract.md`.
- Tenant scoping is mandatory for all tenant-owned data.
- Idempotent ingestion and append-only audit trails are first-class design constraints.
