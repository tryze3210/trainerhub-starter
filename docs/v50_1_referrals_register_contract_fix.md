# TrainerHub v50.1 — referrals register contract fix

Fixes the broken integration seam where `tests/test_referrals_v50_integration.py` passes `referral_invite_id` into `register_user()`, but `apps.authn.services.register_user()` still has the old v49 signature.

The fixer is intentionally idempotent and safe to run over a partially applied v50 patch.

It updates:

- `apps.authn.services.register_user()` signature
- signup referral binding after account creation
- `RegisterSerializer` referral fields
- checkout referral fields and binding
- payment success referral reward hook
- referrals app/URL registration if missing
- `apps.referrals.services.integration` bridge file

Validation command:

```bash
cd backend
python manage.py check
pytest tests/test_referrals_v50_integration.py -q
```
