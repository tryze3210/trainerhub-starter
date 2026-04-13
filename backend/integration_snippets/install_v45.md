# v45 install

1. Add `apps.live_sessions` to `INSTALLED_APPS`
2. Include `apps.live_sessions.api.urls` under `/api/v1/live/`
3. Run:

```bash
python manage.py makemigrations live_sessions
python manage.py migrate
```

4. Wire Celery tasks from `celery_v45.py`
5. Connect booking-to-live bridge from `booking_hooks_v45.py`
6. Connect notifications trigger bridge from `notification_hooks_v45.py`
