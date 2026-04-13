# v33 install

1. Copy backend/apps/notifications changes over v32.
2. Ensure `apps.notifications` is in `INSTALLED_APPS`.
3. Include `apps.notifications.api.urls` under `/api/v1/notifications/`.
4. Run migrations:
   ```bash
   python manage.py migrate
   ```
5. Seed templates for email delivery.
6. Add Celery beat schedule from `backend/integration_snippets/celery.py`.
7. Restart backend, celery worker, celery beat.
8. Copy frontend files and add admin route link.

## Required settings

```python
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="noreply@example.com")
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = env("EMAIL_HOST", default="localhost")
EMAIL_PORT = env.int("EMAIL_PORT", default=25)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=False)
```

## Required template seeds

- `order_paid_email`
- `payment_failed_email`
- `subscription_activated_email`
