# Testing Strategy

The project follows TDD throughout. The current repository state establishes the baseline testing shape.

## Test layers

- Unit tests for isolated domain logic
- Integration tests for database-backed workflows and transaction boundaries
- Contract tests against the OpenAPI definition
- Platform-normalization tests for platform-native to canonical mapping and field derivation
- Security-negative tests for tenant isolation and authorization
- Golden fixture and replay tests for ingestion ordering and idempotency

## Current baseline

- The contract test harness asserts the OpenAPI version and required placeholder paths.
- The harness should expand over time to check request and response shape against implemented handlers.
- Persistence-service unit tests currently lock in exception bubbling from repository errors; API-layer translation is handled separately.

## Future direction

- As API error handling matures, persistence failures may move from raw exception bubbling to explicit domain-level error wrapping with dedicated translation tests.
