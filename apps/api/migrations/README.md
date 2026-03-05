# Migrations

Alembic manages PostgreSQL schema changes for the API service.

From the repository root:

- apply latest migration: `make db-upgrade`
- roll back one migration: `make db-downgrade`
- view migration history: `make db-history`

The initial migration introduces tenancy-first foundations:

- `tenants`
- `users`
- `service_principals`

