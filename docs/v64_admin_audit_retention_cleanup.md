# v64 — Admin audit retention cleanup

Adds a confirmed, bounded cleanup action for old audit events.

## Endpoint

`POST /api/v1/audit/admin/retention/cleanup/`

The endpoint is admin-only and requires explicit confirmation:

```json
{
  "confirm": true,
  "older_than_days": 180,
  "batch_size": 100
}
```

## Safety rules

- No deletion happens unless `confirm=true` is provided.
- Only events with `created_at < now - older_than_days` are eligible.
- `batch_size` is clamped to the same safe limit as preview.
- Existing audit filters are respected.
- Fresh events are never deleted by the retention cutoff.
- Every successful cleanup writes `admin.audit.retention.cleanup`.

## Response

The response includes `deleted_count`, `candidates_total`, `has_more`, filters, cutoff, and the audit event id for the cleanup action.
