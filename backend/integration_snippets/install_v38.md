# v38 install

1. Add `apps.moderation` to `INSTALLED_APPS`.
2. Include `apps.moderation.api.urls` under `/api/v1/moderation/`.
3. Run migrations.
4. Hook moderation case creation from trainer onboarding and content publish flows.
5. Optionally connect notifications when a case is resolved or marked as needs_changes.
