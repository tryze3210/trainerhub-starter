# SIZE CHECK — v68 payout admin frontend dashboard

Generated before archive creation with `wc -c`.

```text
12520 frontend/src/modules/admin-payouts/api.ts
32842 frontend/src/modules/admin-payouts/components/admin-payout-operations-dashboard.tsx
  873 docs/v68_payout_admin_frontend_dashboard.md
  729 MANIFEST.md
 1602 README.md
48566 total
```

## Replacement safety

Existing files replaced by this archive:

| File | New size | Safety note |
| --- | ---: | --- |
| `frontend/src/modules/admin-payouts/api.ts` | 12,520 bytes | Complete replacement; expands admin-payouts API with v65-v67 admin-ops methods and CSV downloader. |
| `frontend/src/modules/admin-payouts/components/admin-payout-operations-dashboard.tsx` | 32,842 bytes | Complete replacement; preserves existing payout workflow controls and adds admin-ops summary/CSV/reconciliation snapshot UI. |

New files:

| File | Size |
| --- | ---: |
| `docs/v68_payout_admin_frontend_dashboard.md` | 873 bytes |
| `MANIFEST.md` | 729 bytes |
| `README.md` | 1,602 bytes |

## Files intentionally not included

- `frontend/src/modules/admin-shell/admin-shell.tsx`
- `frontend/tests/contracts/api-contract.test.js`
- `frontend/tsconfig.tsbuildinfo`
- `backend/**`
- `scripts/**`
- `patches/**`
- `snippets/**`
- `node_modules/**`
- `__pycache__/**`
- `*.pyc`

## Local pre-copy check

Because your local tree has many incremental v50-v67 changes, run this before applying if you want to compare local sizes:

```bash
cd /home/tryze/Рабочий\ стол/мои\ работы/trainerhub-starter
wc -c frontend/src/modules/admin-payouts/api.ts \
      frontend/src/modules/admin-payouts/components/admin-payout-operations-dashboard.tsx
```

The replacement files in this archive are intentionally larger than the current upstream frontend payout API/dashboard files inspected for v68, and the archive avoids overwriting known high-risk files such as `api-contract.test.js` and `admin-shell.tsx`.
