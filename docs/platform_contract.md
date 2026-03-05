# Platform Contract

This document defines the external trading-platform boundary the system connects to. It is intentionally separate from the backend API OpenAPI contract.

## Purpose

The backend should treat upstream platforms such as Sierra Chart, Rithmic, NinjaTrader, or a future simulator as external systems with platform-specific payloads and capabilities.

The connection layer is responsible for:

- fetching platform-native data
- normalizing it into the canonical model used by ingestion and risk evaluation
- deriving fields that are absent but safely inferable

## Design constraints

- The backend must not depend on any single platform's field names or payload shape outside the connection layer.
- Connectors may differ in authentication, pagination, polling cadence, and available fields.
- Missing fields may be derived only when the derivation rule is explicit and testable.
- Derived fields should be recorded as derived, not silently treated as native platform values.

## Minimal external capabilities

Each supported platform should provide, directly or indirectly, enough information to produce:

- stable external account identifier
- current balance
- daily profit and loss, or equivalent data needed to derive it
- fills or executions with stable source identifiers
- event ordering metadata or polling/cursor metadata

## Example derivation rules

- `starting_balance = current_balance - daily_pnl`
- if a platform exposes realized and unrealized P&L separately, connector logic may define how daily P&L is assembled before normalization

## Connector responsibilities

- handle platform-specific auth and request semantics
- model platform-native payloads
- expose connector capabilities such as whether starting balance is native or derived
- normalize platform-native snapshots and fills into canonical backend models

## Candidate platform endpoints

This is a conceptual interface, not a required literal HTTP shape for every platform:

- `GET /accounts`
- `GET /accounts/{account_id}/balances`
- `GET /accounts/{account_id}/positions`
- `GET /fills?since=<cursor>`
- `GET /orders?since=<cursor>`
- `GET /health` or equivalent heartbeat

## Failure modes the connection layer must tolerate

- duplicate fills
- out-of-order fills
- delayed platform updates
- partial account data
- transient platform errors and retries

## Relationship to the simulator

A future simulator should implement this external platform contract as a standalone app. Inside the backend codebase, the simulator belongs as another platform adapter target under the `connections` boundary, not as backend business logic.

## Platform-specific mappings

Use platform-specific docs for concrete field maps and phased scope:

- `docs/platforms/sierra_chart_dtc.md`
