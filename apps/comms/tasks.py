from celery import shared_task

from .selectors import get_due_messages
from .services import MessageDispatchService


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 5})
def dispatch_due_notifications(self, limit: int = 100):
    service = MessageDispatchService()
    processed = 0
    for message in get_due_messages(limit=limit):
        service.dispatch(message=message)
        processed += 1
    return {"processed": processed}
