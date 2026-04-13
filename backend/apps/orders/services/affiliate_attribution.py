from apps.affiliates.services import AffiliateCommissionService


def attach_affiliate_attribution_to_order(*, order, user=None, client_key: str | None = None):
    return AffiliateCommissionService.attribute_order(order=order, user=user, client_key=client_key)
