# v46 install

1. Add `apps.cohorts` to `INSTALLED_APPS`
2. Include `apps.cohorts.api.urls` under `/api/v1/cohorts/`
3. Generate and apply migrations:
   ```bash
   python manage.py makemigrations cohorts
   python manage.py migrate
   ```
4. Wire nightly dashboard rebuild task from `celery_v46.py`
5. Connect enrollment activation to order/payment/entitlement application services
6. Connect attendance rate enrichment to `live_sessions`
