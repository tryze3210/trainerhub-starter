from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, response, status, views

from apps.moderation.api.serializers import (
    ModerationAssignSerializer,
    ModerationCaseDetailSerializer,
    ModerationCaseSerializer,
    ModerationDecisionInputSerializer,
    TrainerRiskFlagCreateSerializer,
    TrainerRiskFlagSerializer,
)
from apps.moderation.domain.models import ModerationCase, TrainerRiskFlag
from apps.moderation.services import ModerationCaseService, TrainerRiskService
from apps.trainers.services.maintenance import TrainerMarketplaceMaintenanceService


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
        search = self.request.query_params.get("search")
        if status_value:
            qs = qs.filter(status=status_value)
        if queue:
            qs = qs.filter(queue=queue)
        if search:
            qs = qs.filter(Q(title__icontains=search) | Q(summary__icontains=search) | Q(target_id__icontains=search))
        return qs.order_by("priority", "-opened_at")


class AdminModerationOverviewView(views.APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        status_totals = ModerationCase.objects.aggregate(
            total=Count("id"),
            open=Count("id", filter=Q(status="open")),
            in_review=Count("id", filter=Q(status="in_review")),
            escalated=Count("id", filter=Q(status="escalated")),
            resolved=Count("id", filter=Q(status="resolved")),
        )
        queue_rows = (
            ModerationCase.objects.values("queue")
            .annotate(total=Count("id"), open=Count("id", filter=Q(status__in=["open", "in_review", "escalated"])))
            .order_by("queue")
        )
        risk_rows = (
            TrainerRiskFlag.objects.filter(is_active=True)
            .values("risk_level")
            .annotate(count=Count("id"))
            .order_by("risk_level")
        )
        latest_cases = ModerationCase.objects.select_related("trainer", "assigned_to").order_by("-opened_at")[:10]
        data = {
            "totals": status_totals,
            "queues": list(queue_rows),
            "risk_levels": list(risk_rows),
            "active_risk_flags": TrainerRiskFlag.objects.filter(is_active=True).count(),
            "latest_cases": ModerationCaseSerializer(latest_cases, many=True).data,
        }
        return response.Response(data)


class AdminModerationCaseDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = ModerationCaseDetailSerializer
    lookup_url_kwarg = "case_id"

    def get_queryset(self):
        return ModerationCase.objects.select_related("trainer", "assigned_to").prefetch_related("events", "decisions")


class AdminModerationCaseAssignView(views.APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, case_id):
        serializer = ModerationAssignSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        case = get_object_or_404(ModerationCase, id=case_id)
        assignee_id = serializer.validated_data.get("assignee_id")
        assignee = request.user
        if assignee_id:
            assignee = get_object_or_404(get_user_model(), id=assignee_id)
        updated = ModerationCaseService().assign_case(case=case, actor=request.user, assignee=assignee)
        return response.Response(ModerationCaseDetailSerializer(updated).data)


class AdminModerationDecisionCreateView(views.APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, case_id):
        serializer = ModerationDecisionInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        case = get_object_or_404(ModerationCase, id=case_id)
        updated = ModerationCaseService().submit_decision(
            case=case,
            reviewer=request.user,
            decision=serializer.validated_data["decision"],
            reason=serializer.validated_data.get("reason", ""),
            metadata=serializer.validated_data.get("metadata") or {},
        )
        return response.Response(ModerationCaseDetailSerializer(updated).data, status=status.HTTP_200_OK)


class AdminMarketplaceCoreMaintenanceView(views.APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        return response.Response(TrainerMarketplaceMaintenanceService().inspect())

    def post(self, request):
        dry_run = request.data.get("dry_run", True)
        if isinstance(dry_run, str):
            dry_run = dry_run.lower() not in {"0", "false", "no", "apply"}
        else:
            dry_run = bool(dry_run)
        report = TrainerMarketplaceMaintenanceService().repair(dry_run=dry_run)
        return response.Response(report.as_dict(), status=status.HTTP_200_OK)


class AdminTrainerRiskFlagsView(generics.ListAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = TrainerRiskFlagSerializer

    def get_queryset(self):
        qs = TrainerRiskFlag.objects.select_related("trainer")
        trainer_id = self.request.query_params.get("trainer_id")
        active = self.request.query_params.get("active")
        if trainer_id:
            qs = qs.filter(trainer_id=trainer_id)
        if active in {"1", "true", "yes"}:
            qs = qs.filter(is_active=True)
        return qs.order_by("-created_at")


class AdminTrainerRiskFlagCreateView(views.APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        serializer = TrainerRiskFlagCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        trainer = get_object_or_404(get_user_model(), id=serializer.validated_data["trainer_id"])
        flag = TrainerRiskService().raise_flag(
            trainer=trainer,
            code=serializer.validated_data["code"],
            label=serializer.validated_data["label"],
            risk_level=serializer.validated_data["risk_level"],
            source="admin_manual",
            details=serializer.validated_data.get("details") or {},
        )
        return response.Response(TrainerRiskFlagSerializer(flag).data, status=status.HTTP_201_CREATED)


class AdminTrainerRiskFlagResolveView(views.APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, flag_id):
        flag = get_object_or_404(TrainerRiskFlag, id=flag_id)
        updated = TrainerRiskService().resolve_flag(flag=flag)
        return response.Response(TrainerRiskFlagSerializer(updated).data)


class TrainerModerationStatusView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        cases = ModerationCase.objects.filter(trainer=request.user).order_by("-opened_at")[:20]
        flags = TrainerRiskFlag.objects.filter(trainer=request.user, is_active=True).order_by("-created_at")
        return response.Response(
            {
                "cases": ModerationCaseSerializer(cases, many=True).data,
                "risk_flags": TrainerRiskFlagSerializer(flags, many=True).data,
            }
        )


from apps.events.services import DomainEventService
from apps.moderation.projections import PAYMENT_RISK_QUEUE, moderation_risk_projection_service


class AdminPaymentRiskDashboardView(views.APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        return response.Response(moderation_risk_projection_service.projection_health())


class AdminPaymentRiskCasesView(generics.ListAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = ModerationCaseSerializer

    def get_queryset(self):
        qs = ModerationCase.objects.select_related('trainer', 'assigned_to').filter(queue=PAYMENT_RISK_QUEUE)
        status_value = self.request.query_params.get('status')
        trainer_id = self.request.query_params.get('trainer_id')
        search = self.request.query_params.get('search')
        if status_value:
            qs = qs.filter(status=status_value)
        if trainer_id:
            qs = qs.filter(trainer_id=trainer_id)
        if search:
            qs = qs.filter(Q(title__icontains=search) | Q(summary__icontains=search) | Q(target_id__icontains=search))
        return qs.order_by('priority', '-opened_at')


class AdminPaymentRiskProjectOutboxView(views.APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        batch_size = request.data.get('batch_size', 100)
        try:
            batch_size = int(batch_size)
        except (TypeError, ValueError):
            batch_size = 100
        batch_size = max(1, min(batch_size, 500))
        result = DomainEventService().dispatch_pending_batch(batch_size=batch_size)
        return response.Response(result, status=status.HTTP_200_OK)
