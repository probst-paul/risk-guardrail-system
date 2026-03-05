# ADR 0002: External Platform Connections Boundary

## Status

Accepted

## Context

The system will integrate with multiple external trading platforms such as Sierra Chart, Rithmic, NinjaTrader, and a future simulator. Those platforms expose similar business information with different payload shapes, capabilities, and operational constraints.

Without an explicit boundary, platform-specific logic would leak into backend handlers and risk logic.

## Decision

Create a dedicated `app/connections/` boundary inside the API codebase for:

- platform capability metadata
- platform-native models
- normalization into canonical backend models
- explicit derivation rules for inferable fields
- adapter registration and lookup

The backend OpenAPI contract remains separate from the external platform contract documented in `docs/platform_contract.md`.

## Consequences

- Platform-specific concerns stay isolated from core backend logic
- Derived-field behavior becomes explicit and testable
- Adding a future simulator remains straightforward because it is treated as another external platform target
- Connector and polling concerns can evolve later without changing the core domain boundary

