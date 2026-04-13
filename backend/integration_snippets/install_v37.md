# v37 install

1. Add `apps.legal_compliance` to `INSTALLED_APPS`.
2. Include `apps.legal_compliance.api.urls` under `/api/v1/legal/`.
3. Create and run real migrations.
4. Wire payout create/finalize flow through `assert_trainer_payout_eligible()`.
5. Seed active legal docs:
   - offer
   - terms_of_service
   - privacy_policy
   - trainer_agreement
6. Connect contract artifact generation to finance_documents artifact pipeline from v36.
