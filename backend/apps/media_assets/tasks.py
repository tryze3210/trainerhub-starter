from celery import shared_task


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=5)
def process_media_asset(self, asset_id: str):
    """Placeholder for probe/transcode/thumb generation pipeline."""
    return {"asset_id": asset_id, "status": "scheduled"}
