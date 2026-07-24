"""
Wire these calls inside your existing service layer.
This file is intentionally illustrative and should be adapted to actual imports.
"""

from apps.billing.services.posting import LedgerPostingService


def on_order_payment_settled(*, order, payment, entitlement=None):
    return LedgerPostingService.post_order_payment_settled(
        order=order,
        payment=payment,
        entitlement=entitlement,
    )


def on_subscription_cycle_paid(*, subscription, subscription_cycle, payment, trainer, entitlement=None):
    return LedgerPostingService.post_subscription_payment_settled(
        subscription=subscription,
        subscription_cycle=subscription_cycle,
        payment=payment,
        trainer=trainer,
        entitlement=entitlement,
    )


def on_refund_settled(*, refund):
    return LedgerPostingService.propagate_refund(refund=refund)


def on_entitlement_revoked(*, entitlement, payment):
    return LedgerPostingService.post_entitlement_reversal(
        entitlement=entitlement,
        payment=payment,
    )
