# TrainerHub v60.1 — admin audit API typing fix

Fixes frontend build error introduced by v60 in `frontend/src/modules/admin-audit/api.ts`.

## Problem

`apiRequest()` returns `unknown` unless its generic payload type is specified. `normalizeListResponse<AuditEvent>()` accepts only `AuditEvent[]`, `PaginatedResponse<AuditEvent>`, `null`, or `undefined`, so TypeScript rejected the raw `unknown` payload.

## Fix

The admin audit client now imports `PaginatedResponse`, defines `AuditEventListPayload`, and calls:

```ts
apiRequest<AuditEventListPayload>(...)
```

Runtime behavior is unchanged.
