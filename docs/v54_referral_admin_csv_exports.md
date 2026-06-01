# v54 — Referral admin CSV exports

## Purpose

v52 added admin/ops read APIs for referral rewards, ledger, invites and attributions. v54 adds operational CSV exports for finance/support workflows where an admin needs a filtered extract without direct database access.

## Added endpoints

All endpoints are admin-only and reuse the same filters as the corresponding list endpoints.

- `GET /api/v1/referrals/admin/rewards/export.csv`
- `GET /api/v1/referrals/admin/ledger/export.csv`
- `GET /api/v1/referrals/admin/invites/export.csv`

## Supported filters

Rewards export:

- `status`
- `trigger_type`
- `trigger_reference`
- `owner_id`
- `referred_user_id`
- `program_slug`
- `search`
- `created_from`
- `created_to`

Ledger export:

- `entry_type`
- `owner_id`
- `reward_id`
- `program_slug`
- `search`
- `created_from`
- `created_to`

Invites export:

- `status`
- `code`
- `owner_id`
- `program_slug`
- `click_session_key`
- `utm_campaign`
- `search`
- `created_from`
- `created_to`

## Safety decisions

- Export is capped at `10_000` rows per request to prevent accidental huge responses.
- CSV is UTF-8 with BOM so Russian/European spreadsheet tools open emails, UTM fields and text safely.
- Exports are side-effect free and do not create migrations.
- The implementation reuses existing v52 queryset filters instead of duplicating business conditions.

## Validation

Run:

```bash
cd backend
python manage.py check
python manage.py makemigrations --check --dry-run
pytest tests/test_referrals_v50_integration.py \
       tests/test_referrals_v51_reward_idempotency.py \
       tests/test_referrals_v52_admin_ops_api.py \
       tests/test_referrals_v54_admin_csv_exports.py -q
```
