# v62 — Admin audit retention frontend

Adds read-only retention planning UI to `/admin/audit`.

## Scope

- Adds `adminAuditApi.getRetentionSummary()`.
- Adds `buildAdminAuditRetentionSummaryPath()`.
- Adds retention filter `older_than_days` support to audit query builder.
- Adds `/audit/admin/retention/summary/` to frontend route contracts.
- Adds an Audit retention summary block to the admin audit page.

## Endpoint used

```text
GET /api/v1/audit/admin/retention/summary/
```

Supported filters are inherited from audit feed plus `older_than_days`:

```text
event_type
entity_type
entity_id
actor_id
created_from
created_to
search
older_than_days
```

## Behavior

This UI is read-only. It does not delete audit events. It shows how many audit events are older than the selected retention threshold and breaks them down by event type and entity type.
