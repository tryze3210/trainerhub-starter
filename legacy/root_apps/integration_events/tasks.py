from celery import shared_task

from .selectors import OutboxSelector
from .services import EventPublisherService


@shared_task(bind=True, max_retries=5, default_retry_delay=30)
def publish_due_outbox_events(self, batch_size: int = 100):
    results = []
    for event in OutboxSelector.due_events(limit=batch_size):
        result = EventPublisherService.publish_event(event)
        results.append({"event_id": event.id, "delivered": result.delivered, "failed": result.failed})
    return results
