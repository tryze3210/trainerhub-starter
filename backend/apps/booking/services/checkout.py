from dataclasses import dataclass
from decimal import Decimal


@dataclass
class CheckoutSession:
    reservation_id: str
    amount: Decimal
    currency: str
    status: str
    payment_link_id: str | None = None


class BookingCheckoutService:
    """Integration seam between booking and commerce/payment domains."""

    def create_checkout_for_reservation(self, reservation, amount: Decimal, currency: str = "RUB") -> CheckoutSession:
        return CheckoutSession(
            reservation_id=str(reservation.id),
            amount=amount,
            currency=currency,
            status="pending",
            payment_link_id=None,
        )

    def mark_checkout_paid(self, payment_link, order_id, payment_id) -> None:
        payment_link.order_id = order_id
        payment_link.payment_id = payment_id
        payment_link.checkout_status = "paid"
        payment_link.save(update_fields=["order_id", "payment_id", "checkout_status", "updated_at"])
