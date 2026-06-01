# v53.2 Referral admin frontend — verified files

This patch finalizes the v53 frontend admin integration after the unsafe v53 archive was rolled back.

## Engineering decision

The admin referrals screen is kept as a dedicated App Router page at `/admin/referrals`. The frontend API contract is isolated in `src/modules/referrals/api.ts` instead of expanding the global API type surface. This keeps the growth/ops feature decoupled from the trainer and catalog modules.

## Safety corrections compared with v53

The previous `frontend/tests/contracts/api-contract.test.js` replacement was too small and dropped existing route assertions. v53.2 replaces it with a full file that keeps all existing route checks and appends referral admin endpoints.

`frontend/src/modules/admin-shell/admin-shell.tsx` is also shipped as a full file, but it preserves the existing admin navigation structure and adds only the `Referrals` item under the commercial group.

## Expected checks

```bash
cd frontend
npm run typecheck
npm run build
npm run test:contracts
```

If the frontend folder still has stale TypeScript build info after local builds, do not commit it:

```bash
git checkout -- frontend/tsconfig.tsbuildinfo
```
