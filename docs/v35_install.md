# v35 install

1. Copy `backend/apps/finance_documents` into the project.
2. Add `apps.finance_documents` to `INSTALLED_APPS`.
3. Include `apps.finance_documents.api.urls` under `/api/v1/finance-documents/`.
4. Run migrations:
   ```bash
   python manage.py migrate
   ```
5. Build initial trainer statements:
   ```bash
   python manage.py build_trainer_statements
   ```
6. Add Celery task from `backend/integration_snippets/celery.py`.

## Integration seams
- Replace stub totals in `services/statements.py` with v34 settlement report bindings.
- Persist `rendered_html` artifacts to VK Cloud Object Storage or S3-compatible storage and write the URL into `artifact_path`.
- Add PDF generation if you need immutable downloadable artifacts instead of HTML.
