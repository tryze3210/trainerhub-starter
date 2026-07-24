from apps.finance.models import FinanceOutboxEvent


class FinanceOutboxService:
    @staticmethod
    def publish(*, topic: str, aggregate_type: str, aggregate_id: str, payload: dict) -> FinanceOutboxEvent:
        return FinanceOutboxEvent.objects.create(
            topic=topic,
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            payload=payload,
        )
