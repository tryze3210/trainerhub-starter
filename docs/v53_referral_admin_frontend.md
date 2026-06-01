# TrainerHub v53 — referral admin frontend

## Цель

v52 добавил backend admin ops API для referrals. v53 закрывает операционный frontend:
администратор видит referral attribution, rewards, ledger, invites и integrity snapshot без ручного `curl`/`psql`.

## Добавлено

- `frontend/src/modules/referrals/api.ts`
  - typed client для `/api/v1/referrals/admin/*`
  - локальные типы, чтобы не раздувать общий `@/types/api`
- `frontend/src/app/admin/referrals/page.tsx`
  - KPI: invites, attributions, approved rewards, integrity
  - фильтры: period, status, program slug, search
  - rewards table
  - ledger list
  - invites list
  - attributions list
- `frontend/src/modules/admin-shell/admin-shell.tsx`
  - пункт `Referrals` в commercial admin navigation
- `frontend/tests/contracts/api-contract.test.js`
  - frontend route contract для referral admin endpoints

## Проверка

```bash
cd frontend
npm run typecheck
npm run build
npm run test:contracts
```

Backend после v52 должен отдавать:

```text
GET /api/v1/referrals/admin/ops/overview/
GET /api/v1/referrals/admin/rewards/
GET /api/v1/referrals/admin/ledger/
GET /api/v1/referrals/admin/invites/
GET /api/v1/referrals/admin/attributions/
```

## Инженерное решение

Referral frontend вынесен в отдельный `modules/referrals/api.ts`, а не в общий `src/lib/api.ts`.
Причина: в проекте уже большой legacy-style API facade, и новые growth/ops контракты должны быть изолированы по bounded context.
