from django.db.models import Count, Q
from rest_framework import generics, permissions, response, status, views

from apps.moderation.api.serializers import ModerationCaseSerializer, ModerationDecisionSerializer, TrainerRiskFlagSerializer
from apps.moderation.domain.models import ModerationCase, TrainerRiskFlag
from apps.moderation.services.case_management import ModerationCaseService
from apps.moderation.services.risk import TrainerRiskService


class IsAdminUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_staff)


class AdminModerationQueueView(generics.ListAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = ModerationCaseSerializer

    def get_queryset(self):
        qs = ModerationCase.objects.select_related("trainer", "assigned_to")
        status_value = self.request.query_params.get("status")
        queue = self.request.query_params.get("queue")
        if status_value:
            qs = qs.filter(status=status_value)
        if queue:
            qs = qs.filter(queue=queue)
        return qs.order_by("priority", "-opened_at")


class AdminModerationOverviewView(views.APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        data = {
            "totals": ModerationCase.objects.aggregate(
                total=Count("id"),
                open=Count("id", filter=Q(status="open")),
                in_review=Count("id", filter=Q(status="in_review")),
                escalated=Count("id", filter=Q(status="escalated")),
                resolved=Count("id", filter=Q(status="resolved")),
            ),
            "active_risk_flags": TrainerRiskFlag.objects.filter(is_active=True).count(),
        }
        return response.Response(data)


class AdminModerationDecisionCreateView(views.APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, case_id):
        case = ModerationCase.objects.get(id=case_id)
        service = ModerationCaseService()
        updated = service.submit_decision(
            case=case,
            reviewer=request.user,
            decision=request.data["decision"],
            reason=request.data.get("reason", ""),
            metadata=request.data.get("metadata") or {},
        )
        return response.Response(ModerationCaseSerializer(updated).data, status=status.HTTP_200_OK)


class AdminTrainerRiskFlagsView(generics.ListAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = TrainerRiskFlagSerializer

    def get_queryset(self):
        qs = TrainerRiskFlag.objects.select_related("trainer")
        trainer_id = self.request.query_params.get("trainer_id")
        if trainer_id:
            qs = qs.filter(trainer_id=trainer_id)
        return qs.order_by("-created_at")


class AdminTrainerRiskFlagCreateView(views.APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        trainer = getattr(request.user.__class__, "objects").get(id=request.data["trainer_id"])
        service = TrainerRiskService()
        flag = service.raise_flag(
            trainer=trainer,
            code=request.data["code"],
            label=request.data["label"],
            risk_level=request.data["risk_level"],
            source="admin_manual",
            details=request.data.get("details") or {},
        )
        return response.Response(TrainerRiskFlagSerializer(flag).data, status=status.HTTP_201_CREATED)


class TrainerModerationStatusView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        cases = ModerationCase.objects.filter(trainer=request.user).order_by("-opened_at")[:20]
        flags = TrainerRiskFlag.objects.filter(trainer=request.user, is_active=True).order_by("-created_at")
        return response.Response({
            "cases": ModerationCaseSerializer(cases, many=True).data,
            "risk_flags": TrainerRiskFlagSerializer(flags, many=True).data,
        })
