# v63 — Admin audit retention preview

Adds a read-only cleanup preview endpoint for the audit trail.

## Endpoint

```text
GET /api/v1/audit/admin/retention/preview/
```

## Purpose

The endpoint shows which `AuditEvent` rows would be eligible for a future retention cleanup batch. It never deletes data.

## Query params

- `older_than_days` — retention threshold, clamped to the existing retention max.
- `batch_size` — preview batch size, clamped to `1..1000`.
- `event_type`
- `entity_type`
- `entity_id`
- `actor_id`
- `created_from`
- `created_to`
- `search`

## Response highlights

- `mode = preview`
- `deletion_performed = false`
- `candidates_total`
- `preview_count`
- `has_more`
- `events[]`

This is the safe step before adding any destructive retention cleanup action.
