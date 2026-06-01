# v53.1 safe apply notes

v53.1 is a corrective packaging change for v53.

It avoids overwriting existing files that may already contain many project-specific routes and navigation items.
The only files copied directly are new files:

- `frontend/src/app/admin/referrals/page.tsx`
- `frontend/src/modules/referrals/api.ts`

Existing files should receive only small inserts:

- `frontend/src/modules/admin-shell/admin-shell.tsx`: add the Referrals nav item.
- `frontend/tests/contracts/api-contract.test.js`: add referral route assertions.

If v53 already shrank files, restore them first from git:

```bash
git checkout -- frontend/src/modules/admin-shell/admin-shell.tsx frontend/tests/contracts/api-contract.test.js
```

Then apply v53.1.
