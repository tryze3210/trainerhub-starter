# v49 install

1. Добавь `apps.referrals` в `INSTALLED_APPS`
2. Подключи `apps.referrals.api.urls` под `/api/v1/referrals/`
3. Сгенерируй миграции:
   ```bash
   python manage.py makemigrations referrals
   python manage.py migrate
   ```
4. Засейди стартовый ReferralProgram
5. Подключи integration hooks:
   - registration -> ReferralAttributionService
   - order paid -> ReferralRewardService
6. Подключи celery snippet из `backend/integration_snippets/celery_v49.py`

## Assumptions
- кастомный user model поддерживает `id`
- order/payment confirmation вызывается из application service
- analytics layer может передавать `utm_source`, `utm_medium`, `utm_campaign`
