# v39 install

1. Add `apps.disputes` to `INSTALLED_APPS`.
2. Include `apps.disputes.api.urls` under `/api/v1/disputes/`.
3. Run migrations:
   ```bash
   python manage.py makemigrations disputes
   python manage.py migrate
   ```
4. Wire integration hooks from `backend/integration_snippets/dispute_hooks_v39.py` into payment/refund/chargeback flows.
5. Restart backend, celery worker, celery beat.
6. Copy frontend files and link admin pages.

## Seed recommendation
Create default dispute reasons:
- duplicate_charge
- unauthorized_payment
- content_not_received
- quality_issue
- refund_request
- other
