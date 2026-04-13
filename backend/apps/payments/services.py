from django.utils import timezone
from apps.orders.models import OrderStatus
from apps.payments.gateway import PaymentGatewayAdapter
from apps.payments.models import Payment, PaymentProvider, PaymentStatus, PaymentWebhookEvent
from apps.commerce.services import CommerceFinalizationService


class PaymentService:
    @staticmethod
    def create_checkout_payment(*, order, provider: str = PaymentProvider.MOCK) -> Payment:
        payment = Payment.objects.create(
            order=order,
            provider=provider,
            status=PaymentStatus.PENDING,
            amount=order.total_amount,
            currency=order.currency,
        )
        gateway_payload = PaymentGatewayAdapter().create_checkout(order=order, payment=payment)
        payment.external_payment_id = gateway_payload['external_payment_id']
        payment.external_checkout_url = gateway_payload['checkout_url']
        payment.provider_payload = gateway_payload['payload']
        payment.save(update_fields=['external_payment_id', 'external_checkout_url', 'provider_payload', 'updated_at'])
        return payment

    @staticmethod
    def mark_succeeded(*, payment: Payment, provider_payload: dict | None = None) -> Payment:
        payment.status = PaymentStatus.SUCCEEDED
        payment.provider_payload = provider_payload or payment.provider_payload
        payment.confirmed_at = timezone.now()
        payment.save(update_fields=['status', 'provider_payload', 'confirmed_at', 'updated_at'])

        order = payment.order
        order.status = OrderStatus.PAID
        order.paid_at = timezone.now()
        order.save(update_fields=['status', 'paid_at', 'updated_at'])

        CommerceFinalizationService.finalize_paid_order(order=order)
        return payment


class PaymentWebhookService:
    @staticmethod
    def handle(*, provider: str, event_type: str, external_event_id: str, payload: dict) -> PaymentWebhookEvent:
        event, _ = PaymentWebhookEvent.objects.get_or_create(
            external_event_id=external_event_id,
            defaults={'provider': provider, 'event_type': event_type, 'payload': payload},
        )
        if event.processed_at:
            return event
        payment = Payment.objects.get(external_payment_id=payload['external_payment_id'])
        if event_type == 'payment.succeeded':
            PaymentService.mark_succeeded(payment=payment, provider_payload=payload)
        event.processed_at = timezone.now()
        event.save(update_fields=['processed_at'])
        return event
