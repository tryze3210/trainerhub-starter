# v47 install

1. Add `apps.habits` to `INSTALLED_APPS`
2. Include `apps.habits.api.urls` under `/api/v1/habits/`
3. Generate migrations in project:

```bash
python manage.py makemigrations habits
python manage.py migrate
```

4. Wire reminder schedule from `celery_v47.py`
5. Connect cohort hooks from `cohort_hooks_v47.py`
6. Connect notification bridge from `notification_hooks_v47.py`
