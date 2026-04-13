from apps.affiliates.models import AffiliateCommissionStatus


def record_affiliate_commission_liability(*, commission):
    """
    Expected ledger semantics:
    - debit: affiliate acquisition expense
    - credit: affiliate payable liability
    """
    return {
        "order_id": commission.order_id,
        "partner_id": commission.partner_id,
        "amount": commission.amount,
        "currency": commission.currency,
        "status": commission.status,
        "ledger_hint": "affiliate_commission_accrual",
    }


def reverse_affiliate_commission_liability(*, commission):
    commission.status = AffiliateCommissionStatus.REVERSED
    commission.save(update_fields=["status"])
    return {
        "order_id": commission.order_id,
        "partner_id": commission.partner_id,
        "amount": commission.amount,
        "currency": commission.currency,
        "status": commission.status,
        "ledger_hint": "affiliate_commission_reversal",
    }
