# TrainerHub v52 — Referral Admin Ops API

## Задача

v50/v51 закрыли referral attribution и денежную идемпотентность reward/ledger. v52 добавляет эксплуатационный слой для администратора: списки, фильтры, detail и integrity snapshot без ручных SQL-запросов в production DB.

## Новые endpoints

Все endpoints требуют `IsAdminUser`.

- `GET /api/v1/referrals/admin/ops/overview/?days=30`
- `GET /api/v1/referrals/admin/rewards/`
- `GET /api/v1/referrals/admin/rewards/<reward_id>/`
- `GET /api/v1/referrals/admin/ledger/`
- `GET /api/v1/referrals/admin/invites/`
- `GET /api/v1/referrals/admin/invites/<invite_id>/`
- `GET /api/v1/referrals/admin/attributions/`

## Основные фильтры

Rewards:

- `status`
- `trigger_type`
- `trigger_reference`
- `owner_id`
- `referred_user_id`
- `program_slug`
- `created_from`
- `created_to`
- `search`

Ledger:

- `entry_type`
- `owner_id`
- `reward_id`
- `program_slug`
- `created_from`
- `created_to`
- `search`

Invites:

- `status`
- `code`
- `owner_id`
- `program_slug`
- `click_session_key`
- `utm_campaign`
- `created_from`
- `created_to`
- `search`

Attributions:

- `owner_id`
- `referred_user_id`
- `program_slug`
- `created_from`
- `created_to`
- `search`

## Integrity snapshot

Overview возвращает диагностические счётчики:

- `stale_pending_invites`
- `converted_without_attribution`
- `approved_rewards_without_ledger`
- `rewards_with_multiple_ledger_entries`
- `ledger_reward_entries_without_reward`

Если любой счётчик выше нуля, статус overview становится `warning`.

## Миграции

Нет новых моделей и полей. `makemigrations --check --dry-run` должен пройти без изменений.
