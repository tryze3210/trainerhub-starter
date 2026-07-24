from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable, Optional

from django.db import transaction
from django.utils import timezone

from apps.billing.domain.constants import LedgerAccount, LedgerDirection, LedgerSourceType
from apps.billing.models import LedgerEntry
from apps.billing.services.revenue_split import RevenueSplitService


class AccountingError(Exception):
    pass


@dataclass(frozen=True)
class PostingContext:
    currency: str
    event_at: Optional[object] = None
    metadata: Optional[dict] = None


class LedgerPostingService:
    @staticmethod
    def _create_entry(**kwargs) -> LedgerEntry:
        return LedgerEntry.objects.create(**kwargs)

    @classmethod
    @transaction.atomic
    def post_order_payment_settled(cls, *, order, payment, entitlement=None, idempotency_suffix: str = "settled") -> list[LedgerEntry]:
        if hasattr(payment, "status") and payment.status not in {"paid", "captured", "settled"}:
            raise AccountingError("Payment must be settled before posting accounting entries")

        entries: list[LedgerEntry] = []
        event_at = getattr(payment, "paid_at", None) or timezone.now()

        for item in order.items.select_related("trainer").all():
            trainer = getattr(item, "trainer", None)
            if trainer is None:
                continue

            split = RevenueSplitService.calculate(
                gross_amount=item.total_price,
                trainer=trainer,
                order_item_type=getattr(item, "item_type", None),
            )
            group_key = f"order-payment:{payment.id}:item:{item.id}"

            cash_in = cls._create_entry(
                trainer=trainer,
                user=order.user,
                order=order,
                order_item=item,
                payment=payment,
                entitlement=entitlement,
                account=LedgerAccount.CASH_IN,
                direction=LedgerDirection.CREDIT,
                source_type=LedgerSourceType.ORDER_PAYMENT,
                source_ref=str(payment.id),
                event_at=event_at,
                currency=payment.currency,
                amount=split.gross_amount,
                idempotency_key=f"ledger:order:{order.id}:payment:{payment.id}:item:{item.id}:cash_in:{idempotency_suffix}",
                group_key=group_key,
                metadata={
                    "trainer_share_percent": str(split.trainer_share_percent),
                    "platform_commission_percent": str(split.platform_commission_percent),
                },
            )
            trainer_payable = cls._create_entry(
                trainer=trainer,
                user=order.user,
                order=order,
                order_item=item,
                payment=payment,
                entitlement=entitlement,
                account=LedgerAccount.TRAINER_PAYABLE,
                direction=LedgerDirection.CREDIT,
                source_type=LedgerSourceType.ORDER_PAYMENT,
                source_ref=str(payment.id),
                event_at=event_at,
                currency=payment.currency,
                amount=split.trainer_amount,
                idempotency_key=f"ledger:order:{order.id}:payment:{payment.id}:item:{item.id}:trainer_payable:{idempotency_suffix}",
                group_key=group_key,
                metadata={
                    "trainer_share_percent": str(split.trainer_share_percent),
                    "platform_commission_percent": str(split.platform_commission_percent),
                },
            )
            platform_commission = cls._create_entry(
                trainer=trainer,
                user=order.user,
                order=order,
                order_item=item,
                payment=payment,
                entitlement=entitlement,
                account=LedgerAccount.PLATFORM_COMMISSION_REVENUE,
                direction=LedgerDirection.CREDIT,
                source_type=LedgerSourceType.ORDER_PAYMENT,
                source_ref=str(payment.id),
                event_at=event_at,
                currency=payment.currency,
                amount=split.platform_amount,
                idempotency_key=f"ledger:order:{order.id}:payment:{payment.id}:item:{item.id}:platform_commission:{idempotency_suffix}",
                group_key=group_key,
                metadata={
                    "trainer_share_percent": str(split.trainer_share_percent),
                    "platform_commission_percent": str(split.platform_commission_percent),
                },
            )
            entries.extend([cash_in, trainer_payable, platform_commission])

        return entries

    @classmethod
    @transaction.atomic
    def post_subscription_payment_settled(
        cls,
        *,
        subscription,
        subscription_cycle,
        payment,
        trainer,
        entitlement=None,
        plan_code: Optional[str] = None,
        idempotency_suffix: str = "settled",
    ) -> list[LedgerEntry]:
        gross_amount = getattr(subscription_cycle, "charged_amount", None) or payment.amount
        split = RevenueSplitService.calculate(
            gross_amount=gross_amount,
            trainer=trainer,
            subscription_plan_code=plan_code or getattr(subscription, "plan_code", None),
        )
        event_at = getattr(payment, "paid_at", None) or timezone.now()
        group_key = f"subscription-payment:{payment.id}:cycle:{subscription_cycle.id}"

        common_kwargs = dict(
            trainer=trainer,
            user=subscription.user,
            payment=payment,
            subscription=subscription,
            subscription_cycle=subscription_cycle,
            entitlement=entitlement,
            source_type=LedgerSourceType.SUBSCRIPTION_PAYMENT,
            source_ref=str(payment.id),
            event_at=event_at,
            currency=payment.currency,
            group_key=group_key,
            metadata={
                "trainer_share_percent": str(split.trainer_share_percent),
                "platform_commission_percent": str(split.platform_commission_percent),
            },
        )

        return [
            cls._create_entry(
                **common_kwargs,
                account=LedgerAccount.CASH_IN,
                direction=LedgerDirection.CREDIT,
                amount=split.gross_amount,
                idempotency_key=f"ledger:subscription:{subscription.id}:cycle:{subscription_cycle.id}:payment:{payment.id}:cash_in:{idempotency_suffix}",
            ),
            cls._create_entry(
                **common_kwargs,
                account=LedgerAccount.TRAINER_PAYABLE,
                direction=LedgerDirection.CREDIT,
                amount=split.trainer_amount,
                idempotency_key=f"ledger:subscription:{subscription.id}:cycle:{subscription_cycle.id}:payment:{payment.id}:trainer_payable:{idempotency_suffix}",
            ),
            cls._create_entry(
                **common_kwargs,
                account=LedgerAccount.PLATFORM_COMMISSION_REVENUE,
                direction=LedgerDirection.CREDIT,
                amount=split.platform_amount,
                idempotency_key=f"ledger:subscription:{subscription.id}:cycle:{subscription_cycle.id}:payment:{payment.id}:platform_commission:{idempotency_suffix}",
            ),
        ]

    @classmethod
    @transaction.atomic
    def propagate_refund(cls, *, refund, reversal_reason: str = "refund") -> list[LedgerEntry]:
        if hasattr(refund, "status") and refund.status not in {"paid", "succeeded", "settled", "completed"}:
            raise AccountingError("Refund must be settled before posting reversals")

        payment = refund.payment
        original_entries = LedgerEntry.objects.filter(
            payment=payment,
            reversal_of__isnull=True,
            account__in=[
                LedgerAccount.CASH_IN,
                LedgerAccount.TRAINER_PAYABLE,
                LedgerAccount.PLATFORM_COMMISSION_REVENUE,
            ],
        ).select_related("trainer", "user", "order", "order_item", "subscription", "subscription_cycle", "entitlement")

        created: list[LedgerEntry] = []
        refund_amount = refund.amount
        total_original_gross = sum((entry.amount for entry in original_entries if entry.account == LedgerAccount.CASH_IN), Decimal("0.00"))
        if total_original_gross <= Decimal("0.00"):
            raise AccountingError("No original cash-in entries found for refund propagation")

        ratio = (refund_amount / total_original_gross)
        event_at = getattr(refund, "processed_at", None) or timezone.now()

        for entry in original_entries:
            reversal_amount = RevenueSplitService.quantize(entry.amount * ratio)
            reversal_direction = LedgerDirection.DEBIT if entry.direction == LedgerDirection.CREDIT else LedgerDirection.CREDIT
            created.append(
                cls._create_entry(
                    trainer=entry.trainer,
                    user=entry.user,
                    order=entry.order,
                    order_item=entry.order_item,
                    payment=entry.payment,
                    refund=refund,
                    subscription=entry.subscription,
                    subscription_cycle=entry.subscription_cycle,
                    entitlement=entry.entitlement,
                    account=entry.account,
                    direction=reversal_direction,
                    source_type=LedgerSourceType.REFUND,
                    source_ref=str(refund.id),
                    event_at=event_at,
                    currency=entry.currency,
                    amount=reversal_amount,
                    idempotency_key=f"ledger:refund:{refund.id}:reverse:{entry.id}:{reversal_reason}",
                    group_key=f"refund:{refund.id}",
                    reversal_of=entry,
                    metadata={
                        **entry.metadata,
                        "reversal_reason": reversal_reason,
                        "refund_ratio": str(ratio),
                    },
                )
            )

        return created

    @classmethod
    @transaction.atomic
    def post_entitlement_reversal(
        cls,
        *,
        entitlement,
        payment,
        reason: str = "entitlement_revoked",
    ) -> list[LedgerEntry]:
        target_entries = LedgerEntry.objects.filter(
            entitlement=entitlement,
            payment=payment,
            reversal_of__isnull=True,
            account__in=[LedgerAccount.TRAINER_PAYABLE, LedgerAccount.PLATFORM_COMMISSION_REVENUE],
        )

        created = []
        for entry in target_entries:
            created.append(
                cls._create_entry(
                    trainer=entry.trainer,
                    user=entry.user,
                    order=entry.order,
                    order_item=entry.order_item,
                    payment=entry.payment,
                    subscription=entry.subscription,
                    subscription_cycle=entry.subscription_cycle,
                    entitlement=entry.entitlement,
                    account=entry.account,
                    direction=LedgerDirection.DEBIT if entry.direction == LedgerDirection.CREDIT else LedgerDirection.CREDIT,
                    source_type=LedgerSourceType.ENTITLEMENT_REVERSAL,
                    source_ref=f"entitlement:{entitlement.id}",
                    event_at=timezone.now(),
                    currency=entry.currency,
                    amount=entry.amount,
                    idempotency_key=f"ledger:entitlement:{entitlement.id}:payment:{payment.id}:reverse:{entry.id}:{reason}",
                    group_key=f"entitlement-reversal:{entitlement.id}:{payment.id}",
                    reversal_of=entry,
                    metadata={**entry.metadata, "reversal_reason": reason},
                )
            )
        return created
