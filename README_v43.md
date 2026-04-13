# trainerhub v43 patch

This patch adds a production-oriented messaging slice:
- conversation inbox
- booking-linked threads
- message delivery/read state
- realtime-ready API seam
- admin and trainer messaging pages

## Install
1. Add `apps.messaging` to `INSTALLED_APPS`
2. Include `apps.messaging.api.urls` under `/api/v1/messaging/`
3. Run migrations:
   ```bash
   python manage.py makemigrations messaging
   python manage.py migrate
   ```
4. Wire realtime transport from `backend/integration_snippets/realtime_v43.py`
5. Update frontend pages and API client.
