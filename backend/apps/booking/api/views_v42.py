from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated


class MyCancellationPolicyView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"detail": "trainer cancellation policy payload"})

    def patch(self, request):
        return Response({"detail": "cancellation policy updated"})


class ReservationCheckoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, reservation_id):
        return Response({"detail": "checkout session created", "reservation_id": str(reservation_id)})


class ReservationCancelQuoteView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, reservation_id):
        return Response({"detail": "cancellation quote", "reservation_id": str(reservation_id)})


class ReservationCancelView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, reservation_id):
        return Response({"detail": "reservation cancelled", "reservation_id": str(reservation_id)})


class ReservationInviteResendView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, reservation_id):
        return Response({"detail": "invite resend scheduled", "reservation_id": str(reservation_id)})
