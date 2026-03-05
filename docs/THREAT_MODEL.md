# Threat Model

## Current status

This file is intentionally a scaffold. Detailed threat analysis belongs in the hardening phase, but the first commit records the baseline concerns so later implementation work stays aligned.

## Primary threats

- Cross-tenant data access caused by missing or inconsistent tenant guards
- Over-privileged credentials for service principals or operators
- Duplicate or reordered event delivery causing incorrect risk state
- Missing audit evidence for policy changes and unlock actions
- Sensitive trading or identity data leaking through logs, traces, or error payloads

## Design responses to enforce

- Deny-by-default authorization
- Tenant scoping derived from validated identity claims
- Append-only audit logging for operator actions
- Idempotent ingestion with uniqueness constraints
- Structured logs with sensitive-field hygiene
