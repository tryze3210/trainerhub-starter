from __future__ import annotations

from django.db.models import Q
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from apps.payouts.api.serializers import (
    AdminPayoutBulkTransitionSerializer,
    AdminPayoutDecisionSerializer,
    AdminPayoutOverviewSerializer,
    AdminPayoutRepairSerializer,
    CreatePayoutRequestSerializer,
    PayoutRequestDetailSerializer,
    PayoutRequestSerializer,
    TrainerBalanceSerializer,
)
from apps.payouts.models import PayoutRequest
from apps.payouts.selectors import (
    get_admin_payout_operations_overview,
    get_balance_for_trainer,
    list_all_payout_requests,
    list_payout_requests_for_trainer,
)
from apps.payouts.services import PayoutService


class MyPayoutViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = PayoutRequestSerializer

    def _trainer_id(self):
        return self.request.user.id

    def get_queryset(self):
        return list_payout_requests_for_trainer(self._trainer_id())

    def get_serializer_class(self):
        if self.action == "retrieve":
            return PayoutRequestDetailSerializer
        return super().get_serializer_class()

    @action(methods=["get"], detail=False, url_path="balance")
    def balance(self, request):
        balance = get_balance_for_trainer(self._trainer_id())
        if not balance:
            balance = PayoutService.get_or_create_balance(trainer_id=self._trainer_id())
        return Response(TrainerBalanceSerializer(balance).data)

    @action(methods=["post"], detail=False, url_path="request")
    def request_payout(self, request):
        serializer = CreatePayoutRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payout = PayoutService.request_payout(
            trainer_id=self._trainer_id(),
            amount=serializer.validated_data["amount"],
            destination_masked=serializer.validated_data["destination_masked"],
            request=request,
        )
        return Response(PayoutRequestDetailSerializer(payout).data, status=status.HTTP_201_CREATED)


class AdminPayoutViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    permission_classes = [IsAdminUser]
    serializer_class = PayoutRequestDetailSerializer

    def get_queryset(self):
        queryset = list_all_payout_requests()
        status_filter = (self.request.query_params.get("status") or "").strip()
        trainer_filter = (self.request.query_params.get("trainer_id") or "").strip()
        if status_filter:
            if status_filter == PayoutRequest.Status.PENDING:
                queryset = queryset.filter(status__in=[PayoutRequest.Status.PENDING, PayoutRequest.Status.REQUESTED])
            else:
                queryset = queryset.filter(status=status_filter)
        if trainer_filter:
            queryset = queryset.filter(Q(trainer__user_id=trainer_filter) | Q(trainer_id=trainer_filter))
        return queryset

    @action(methods=["get"], detail=False, url_path="overview")
    def overview(self, request):
        payload = get_admin_payout_operations_overview()
        return Response(AdminPayoutOverviewSerializer(payload).data)

    @action(methods=["post"], detail=True, url_path="transition")
    def transition(self, request, pk=None):
        payout = self.get_object()
        serializer = AdminPayoutDecisionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payout = PayoutService.transition(
            payout=payout,
            action=serializer.validated_data["action"],
            actor=request.user,
            request=request,
            reason=serializer.validated_data.get("reason", ""),
            external_reference=serializer.validated_data.get("external_reference", ""),
        )
        return Response(PayoutRequestDetailSerializer(payout).data)

    @action(methods=["post"], detail=False, url_path="bulk-transition")
    def bulk_transition(self, request):
        serializer = AdminPayoutBulkTransitionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ids = [str(value) for value in serializer.validated_data["payout_ids"]]
        payouts = {str(payout.id): payout for payout in PayoutRequest.objects.filter(id__in=ids)}
        results = []
        for payout_id in ids:
            payout = payouts.get(payout_id)
            if not payout:
                results.append({"id": payout_id, "ok": False, "error": "Payout request not found."})
                continue
            try:
                updated = PayoutService.transition(
                    payout=payout,
                    action=serializer.validated_data["action"],
                    actor=request.user,
                    request=request,
                    reason=serializer.validated_data.get("reason", ""),
                    external_reference=serializer.validated_data.get("external_reference", ""),
                )
                results.append({"id": str(updated.id), "ok": True, "status": PayoutService._canonical_status(updated.status)})
            except ValidationError as exc:
                results.append({"id": payout_id, "ok": False, "error": exc.detail})
        return Response({"results": results})

    @action(methods=["get"], detail=False, url_path="reconciliation")
    def reconciliation(self, request):
        return Response(PayoutService.build_reconciliation_report())

    @action(methods=["post"], detail=False, url_path="reconciliation/repair")
    def repair_reconciliation(self, request):
        serializer = AdminPayoutRepairSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = PayoutService.repair_reconciliation(
            actor=request.user,
            request=request,
            dry_run=serializer.validated_data["dry_run"],
        )
        return Response(payload)
