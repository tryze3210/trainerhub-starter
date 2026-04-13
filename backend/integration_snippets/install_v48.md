# v48 install

1. Add `apps.gamification` to `INSTALLED_APPS`
2. Include `apps.gamification.api.urls` under `/api/v1/gamification/`
3. Generate and apply migrations:
   ```bash
   python manage.py makemigrations gamification
   python manage.py migrate
   ```
4. Wire Celery Beat from `celery_v48.py`
5. Connect domain hooks from `hooks_v48.py` into habits/cohorts/live_sessions application services
6. Seed `BadgeDefinition` and `RewardRule`
