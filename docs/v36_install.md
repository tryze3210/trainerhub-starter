# v36 install

## What this patch adds
- PDF artifact generation pipeline for finance documents
- object storage integration seam for VK Cloud S3-compatible storage
- signed download URLs
- email delivery flow for ready documents

## Install order
1. Apply patch over v35.
2. Extend `FinanceDocument` model with the fields from migration `0002_finance_document_artifacts.py`.
3. Add `FinanceDocumentDelivery` model.
4. Wire `api/urls_v36.py` into `apps.finance_documents.api.urls`.
5. Add settings from `backend/integration_snippets/settings_v36.py`.
6. Install backend dependencies:
   - `weasyprint`
   - `boto3`
   - `botocore`
7. Run migrations.
8. Restart backend, celery worker, celery beat.

## Integration seam
Replace `DummyArtifactStorage` with `VKCloudS3ArtifactStorage` in:
- `services/artifact_pipeline.py`
- `services/download_urls.py`
- `tasks.py`

## Production notes
- Do not expose raw storage URLs. Always return signed URLs.
- Build artifacts asynchronously only.
- Keep artifacts immutable after document finalization.
- Save document HTML snapshot if legal/accounting traceability is required.
