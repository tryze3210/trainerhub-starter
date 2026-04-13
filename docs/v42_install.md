# v42 install

1. Apply patch over v41.
2. Add booking commerce models to `apps.booking`.
3. Include `apps.booking.api.urls_v42`.
4. Generate and apply migrations:

```bash
python manage.py makemigrations booking
python manage.py migrate
```

5. Wire payment success/refund hooks from `backend/integration_snippets/booking_payment_hooks_v42.py`.
6. Enable Celery schedule from `backend/integration_snippets/celery_v42.py`.
7. Expose checkout button and cancellation UX on booking pages.

## New endpoints
- `PATCH /api/v1/booking/me/cancellation-policy/`
- `POST /api/v1/booking/reservations/<uuid>/checkout/`
- `GET /api/v1/booking/reservations/<uuid>/cancel-quote/`
- `POST /api/v1/booking/reservations/<uuid>/cancel/`
- `POST /api/v1/booking/reservations/<uuid>/resend-invite/`
