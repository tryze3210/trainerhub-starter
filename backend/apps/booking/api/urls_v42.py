from django.urls import path
from .views_v42 import (
    MyCancellationPolicyView,
    ReservationCheckoutView,
    ReservationCancelQuoteView,
    ReservationCancelView,
    ReservationInviteResendView,
)

urlpatterns = [
    path("me/cancellation-policy/", MyCancellationPolicyView.as_view()),
    path("reservations/<uuid:reservation_id>/checkout/", ReservationCheckoutView.as_view()),
    path("reservations/<uuid:reservation_id>/cancel-quote/", ReservationCancelQuoteView.as_view()),
    path("reservations/<uuid:reservation_id>/cancel/", ReservationCancelView.as_view()),
    path("reservations/<uuid:reservation_id>/resend-invite/", ReservationInviteResendView.as_view()),
]
