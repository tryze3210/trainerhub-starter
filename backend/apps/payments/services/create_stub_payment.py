from decimal import Decimal
from uuid import uuid4
from django.conf import settings
from django.db import transaction
from apps.payments.models import Payment, PaymentTransaction
from apps.products.models import Product
from apps.purchases.models import Purchase


class CreateStubCheckoutService:
    @transaction.atomic
    def execute(self, *, customer_profile, product: Product):
        gross = product.price_amount
        commission_rate = Decimal(str(settings.GLOBAL_COMMISSION_RATE))
        commission = (gross * commission_rate / Decimal("100")).quantize(Decimal("0.01"))
        trainer_net = (gross - commission).quantize(Decimal("0.01"))

        purchase = Purchase.objects.create(
            customer=customer_profile,
            trainer=product.trainer,
            product=product,
            status="pending",
            gross_amount=gross,
            platform_commission_amount=commission,
            trainer_net_amount=trainer_net,
            currency=product.currency,
        )
        payment = Payment.objects.create(
            customer=customer_profile,
            trainer=product.trainer,
            provider="stub",
            payment_type="one_time",
            status="pending",
            currency=product.currency,
            amount=gross,
            commission_amount=commission,
            trainer_net_amount=trainer_net,
            idempotency_key=f"stub-{uuid4()}",
        )
        PaymentTransaction.objects.create(
            payment=payment,
            provider="stub",
            transaction_type="create_intent",
            status="created",
            response_payload={"purchase_id": str(purchase.id)},
        )
        return purchase, payment
