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

## Planned enforcement

- JWT validation in the backend API
- Tenant guard before handlers reach tenant-owned data
- Query filtering by effective `tenant_id`
- Negative tests for cross-tenant access attempts
