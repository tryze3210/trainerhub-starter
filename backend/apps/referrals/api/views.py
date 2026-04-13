import secrets

from rest_framework import permissions, response, status, views
from rest_framework.generics import ListAPIView

from apps.referrals.api.serializers import (
    GenerateCodeSerializer,
    ReferralCodeSerializer,
    ReferralInviteSerializer,
    ReferralLedgerSerializer,
    ReferralProgramSerializer,
    TrackReferralSerializer,
)
from apps.referrals.models import ReferralCode, ReferralInvite, ReferralLedger, ReferralProgram
from apps.referrals.selectors import get_user_referral_dashboard
from apps.referrals.services import LandingAttributionPayload, ReferralEngine


class MyProgramView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        program = ReferralProgram.objects.filter(is_active=True).order_by("-created_at").first()
        if not program:
            return response.Response({"detail": "No active program"}, status=status.HTTP_404_NOT_FOUND)
        return response.Response(ReferralProgramSerializer(program).data)


class GenerateCodeView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = GenerateCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        program = ReferralProgram.objects.get(slug=serializer.validated_data["program_slug"], is_active=True)
        code = ReferralCode.objects.create(
            owner=request.user,
            program=program,
            code=secrets.token_urlsafe(8).replace("-", "").replace("_", "")[:12].upper(),
        )
        return response.Response(ReferralCodeSerializer(code).data, status=status.HTTP_201_CREATED)


class MyInvitesView(ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ReferralInviteSerializer

    def get_queryset(self):
        return ReferralInvite.objects.filter(code__owner=self.request.user).select_related("code")


class MyRewardsView(ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ReferralLedgerSerializer

    def get_queryset(self):
        return ReferralLedger.objects.filter(owner=self.request.user)


class TrackReferralView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = TrackReferralSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        invite = ReferralEngine.track_landing(
            LandingAttributionPayload(**serializer.validated_data)
        )
        return response.Response({"invite_id": str(invite.id)}, status=status.HTTP_201_CREATED)


class AdminOverviewView(views.APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        data = {
            "programs": ReferralProgram.objects.count(),
            "codes": ReferralCode.objects.count(),
            "invites": ReferralInvite.objects.count(),
            "converted_invites": ReferralInvite.objects.filter(status=ReferralInvite.STATUS_CONVERTED).count(),
            "ledger_entries": ReferralLedger.objects.count(),
        }
        return response.Response(data)


class MyDashboardView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return response.Response(get_user_referral_dashboard(request.user))
