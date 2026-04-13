"""Connect these hooks from your payments/order application services."""


def on_booking_checkout_paid(*, reservation_id, order_id, payment_id):
    # Resolve BookingPaymentLink and mark paid.
    pass


def on_booking_refund_completed(*, reservation_id, refund_id):
    # Update ReservationCancellation.refund_status and emit notification.
    pass
