from django.db.models import Count
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.finance.api.serializers import (
    DiscrepancyResolveInputSerializer,
    ReconciliationDiscrepancySerializer,
    ReconciliationRunInputSerializer,
    ReconciliationSessionSerializer,
    SettlementTransactionSerializer,
)
from apps.finance.models import ReconciliationDiscrepancy, ReconciliationSession, SettlementTransaction
from apps.finance.selectors.reconciliation_selectors import FinanceReconciliationSelector
from apps.finance.services.provider_gateway import ManualSettlementGateway
from apps.finance.services.reconciliation_service import ReconciliationService
from apps.finance.services.repair_service import FinanceRepairService


class IsStaffFinance(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)


class AdminSettlementTransactionViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsStaffFinance]
    serializer_class = SettlementTransactionSerializer

    def get_queryset(self):
        return FinanceReconciliationSelector.settlement_transactions(
            provider=self.request.query_params.get("provider"),
            status=self.request.query_params.get("status"),
        )


class AdminReconciliationSessionViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsStaffFinance]
    serializer_class = ReconciliationSessionSerializer

    def get_queryset(self):
        return FinanceReconciliationSelector.sessions().annotate(discrepancies_count=Count("discrepancies"))

    @action(detail=False, methods=["post"], url_path="run")
    def run_reconciliation(self, request):
        serializer = ReconciliationRunInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        gateway = ManualSettlementGateway()
        service = ReconciliationService(gateway=gateway)
        session = service.run(
            date_from=data["date_from"],
            date_to=data["date_to"],
            started_by=request.user,
        )
        output = self.get_serializer(session)
        return Response(output.data, status=status.HTTP_201_CREATED)


class AdminReconciliationDiscrepancyViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsStaffFinance]
    serializer_class = ReconciliationDiscrepancySerializer

    def get_queryset(self):
        return FinanceReconciliationSelector.discrepancies(status=self.request.query_params.get("status"))

    @action(detail=True, methods=["post"], url_path="resolve")
    def resolve(self, request, pk=None):
        discrepancy = self.get_object()
        serializer = DiscrepancyResolveInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        repair_service = FinanceRepairService()
        target_status = serializer.validated_data.get("target_status")
        if target_status:
            repair_service.force_settlement_status(
                discrepancy=discrepancy,
                target_status=target_status,
                resolved_by=request.user,
                notes=serializer.validated_data["notes"],
            )
        else:
            repair_service.mark_discrepancy_resolved(
                discrepancy=discrepancy,
                resolved_by=request.user,
                notes=serializer.validated_data["notes"],
            )
        discrepancy.refresh_from_db()
        return Response(self.get_serializer(discrepancy).data)
