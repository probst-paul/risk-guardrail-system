# Security Model

## Principles

- Multi-tenancy is a hard boundary, not a convention.
- All access is deny-by-default.
- Service principals are tenant-scoped and purpose-scoped.
- Administrative actions must be attributable and auditable.

## Planned roles

- `viewer`: read-only tenant access
- `risk_admin`: policy edits and unlock operations
- `tenant_admin`: optional tenant administration role
- `service_principal`: ingestion-only machine identity

## Implemented baseline

- Bearer-token request authentication for protected endpoints
- Registered JWT claim checks for issuer, audience, issued-at, and expiry
- Request identity resolution from claims (`sub`, `tenant_id`, `roles`, `principal_type`)
- Tenant guard for effective tenant resolution and cross-tenant override rejection
- Deny-by-default role enforcement for protected admin actions
- Request-level negative tests for authentication and authorization outcomes (`401`/`403`)

## Next enforcement steps

- Signature verification and key management for JWTs (current parser is scaffold-only)
- Service-principal route scoping at endpoint granularity
- Persistent role/source-of-truth integration against database records
- Consistent audit event emission for authorization denials and admin actions
