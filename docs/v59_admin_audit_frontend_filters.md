# TrainerHub v59 — admin audit frontend filters

## Scope

This increment completes the v58 backend audit filter contract on the frontend admin surface.

## Changed files

- `frontend/src/app/admin/audit/page.tsx`
- `frontend/src/modules/admin-audit/api.ts`

## Behavior

The admin audit page now supports:

- free-form `event_type` with presets;
- free-form `entity_type` with presets;
- `entity_id`;
- `actor_id`;
- `created_from`;
- `created_to`;
- `search`;
- `limit` capped by the backend.

The page keeps existing audit cards, action/entity summaries and entity-detail links.

## Production note

This patch intentionally does not touch admin navigation, global route contracts, backend models or migrations.
