from django.db import transaction
from rest_framework.exceptions import ValidationError
from apps.payments.models import Payment, PaymentTransaction
from apps.payouts.models import TrainerWallet, BalanceEntry
from apps.purchases.models import Purchase


class ConfirmStubPaymentService:
    @transaction.atomic
    def execute(self, *, payment: Payment):
        payment = Payment.objects.select_for_update().get(pk=payment.pk)
        if payment.provider != "stub":
            raise ValidationError({"payment": "Only stub payments can be confirmed here."})
        if payment.status == "paid":
            return payment
        if payment.status not in {"pending", "created"}:
            raise ValidationError({"payment": "Payment is not confirmable."})

        purchase = Purchase.objects.select_for_update().get(
            customer=payment.customer,
            trainer=payment.trainer,
            product__trainer=payment.trainer,
            gross_amount=payment.amount,
            status="pending",
        )
        payment.status = "paid"
        payment.save(update_fields=["status", "updated_at"])
        purchase.status = "paid"
        purchase.save(update_fields=["status", "updated_at"])

        wallet, _ = TrainerWallet.objects.get_or_create(trainer=payment.trainer)
        wallet.pending_amount = wallet.pending_amount + payment.trainer_net_amount
        wallet.save(update_fields=["pending_amount", "updated_at"])
        BalanceEntry.objects.create(
            wallet=wallet,
            entry_type="sale_credit",
            direction="credit",
            amount=payment.trainer_net_amount,
            currency=payment.currency,
            status="pending",
            source_type="payment",
            source_id=payment.id,
        )
        PaymentTransaction.objects.create(
            payment=payment,
            provider="stub",
            transaction_type="capture",
            status="paid",
            response_payload={"wallet_id": str(wallet.id)},
        )
        return payment
