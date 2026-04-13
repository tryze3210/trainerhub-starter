# v44 install

1. Add `apps.messaging.models.media` and `apps.messaging.models.escalation` imports into messaging app model registry.
2. Include `apps.messaging.api.urls_v44` into main messaging urls.
3. Generate migrations:
   `python manage.py makemigrations messaging && python manage.py migrate`
4. Replace dummy upload signer with VK Cloud S3 compatible storage adapter.
5. Wire escalation service into support/disputes inbox creation flow.
