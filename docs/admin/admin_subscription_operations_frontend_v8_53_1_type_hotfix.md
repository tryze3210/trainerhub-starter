# v8.53.1 — Admin subscriptions frontend type hotfix

Fixes frontend type errors from v8.53:

- Next.js 15 dynamic page params are now awaited as `Promise<{ subscriptionId: string }>` in `/admin/subscriptions/[subscriptionId]`.
- `AuthUser` compatibility restored by checking only `active_role === 'admin'`; the project type does not expose `is_staff` / `is_superuser` on the frontend user shape.

No backend files are changed.
