from __future__ import annotations

from django.db.models import Q

from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.access_control.permissions import IsFinanceOps
from apps.audit.services import AuditService
from apps.events.services import DomainEventService
from apps.payments.models import Payment
from apps.payouts.api.serializers import (
    AdminPayoutBulkTransitionSerializer,
    AdminPayoutDecisionSerializer,
    AdminPayoutOverviewSerializer,
    AdminPayoutReferenceSerializer,
    AdminPayoutRejectSerializer,
    AdminPayoutRepairSerializer,
    CreatePayoutRequestSerializer,
    ManualPaymentHoldReleaseSerializer,
    PayoutProjectionHealthSerializer,
    PayoutProjectionRunSerializer,
    PayoutRequestDetailSerializer,
    PayoutRequestSerializer,
    PayoutRiskHoldReportSerializer,
    PayoutRiskHoldSerializer,
    TrainerBalanceSerializer,
)
from apps.payouts.models import BalanceEntry, PayoutRequest
from apps.payouts.projections import payout_revenue_projection_service
from apps.payouts.selectors import (
    get_admin_payout_operations_overview,
    get_balance_for_trainer,
    list_all_payout_requests,
    list_payout_requests_for_trainer,
)
from apps.payouts.services import PayoutService
from apps.tenancy.scoping import scope_balance_entries_for_user, scope_payments_for_user, scope_payouts_for_user


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
        balance = get_balance_for_trainer(self._trainer_id()) or payout.wallet
        return Response(
            {
                "payout": PayoutRequestDetailSerializer(payout).data,
                "wallet": TrainerBalanceSerializer(balance).data,
            },
            status=status.HTTP_201_CREATED,
        )


class AdminPayoutViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    permission_classes = [IsFinanceOps]
    serializer_class = PayoutRequestDetailSerializer

    def get_queryset(self):
        queryset = scope_payouts_for_user(list_all_payout_requests(), self.request.user)
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

    def _transition_response(self, *, request, payout: PayoutRequest, action: str, reason: str = "", external_reference: str = ""):
        try:
            updated = PayoutService.transition(
                payout=payout,
                action=action,
                actor=request.user,
                request=request,
                reason=reason,
                external_reference=external_reference,
            )
        except ValidationError:
            raise
        except Exception as exc:
            raise ValidationError({"detail": str(exc)}) from exc
        return Response(PayoutRequestDetailSerializer(updated).data)

    @action(methods=["get"], detail=False, url_path="overview")
    def overview(self, request):
        payload = get_admin_payout_operations_overview()
        return Response(AdminPayoutOverviewSerializer(payload).data)

    @action(methods=["post"], detail=True, url_path="transition")
    def transition(self, request, pk=None):
        payout = self.get_object()
        serializer = AdminPayoutDecisionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return self._transition_response(
            request=request,
            payout=payout,
            action=serializer.validated_data["action"],
            reason=serializer.validated_data.get("reason", ""),
            external_reference=serializer.validated_data.get("external_reference", ""),
        )

    @action(methods=["post"], detail=True, url_path="approve")
    def approve(self, request, pk=None):
        payout = self.get_object()
        serializer = AdminPayoutReferenceSerializer(data=request.data or {})
        serializer.is_valid(raise_exception=True)
        return self._transition_response(
            request=request,
            payout=payout,
            action="approve",
            external_reference=serializer.validated_data.get("external_reference", ""),
        )

    @action(methods=["post"], detail=True, url_path="processing")
    def processing(self, request, pk=None):
        payout = self.get_object()
        serializer = AdminPayoutReferenceSerializer(data=request.data or {})
        serializer.is_valid(raise_exception=True)
        return self._transition_response(
            request=request,
            payout=payout,
            action="processing",
            external_reference=serializer.validated_data.get("external_reference", ""),
        )

    @action(methods=["post"], detail=True, url_path="mark-paid")
    def mark_paid(self, request, pk=None):
        payout = self.get_object()
        serializer = AdminPayoutReferenceSerializer(data=request.data or {})
        serializer.is_valid(raise_exception=True)
        external_reference = serializer.validated_data.get("external_reference", "")
        if payout.status == PayoutRequest.Status.APPROVED:
            payout = PayoutService.transition(
                payout=payout,
                action="processing",
                actor=request.user,
                request=request,
                external_reference=external_reference,
            )
        return self._transition_response(
            request=request,
            payout=payout,
            action="paid",
            external_reference=external_reference,
        )

    @action(methods=["post"], detail=True, url_path="reject")
    def reject(self, request, pk=None):
        payout = self.get_object()
        serializer = AdminPayoutRejectSerializer(data=request.data or {})
        serializer.is_valid(raise_exception=True)
        return self._transition_response(
            request=request,
            payout=payout,
            action="reject",
            reason=serializer.validated_data["reason"],
            external_reference=serializer.validated_data.get("external_reference", ""),
        )

    @action(methods=["post"], detail=False, url_path="bulk-transition")
    def bulk_transition(self, request):
        serializer = AdminPayoutBulkTransitionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ids = [str(value) for value in serializer.validated_data["payout_ids"]]
        payouts = {str(payout.id): payout for payout in scope_payouts_for_user(PayoutRequest.objects.filter(id__in=ids), request.user)}
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

    @action(methods=["get"], detail=False, url_path="projection-health")
    def projection_health(self, request):
        payload = payout_revenue_projection_service.projection_health()
        return Response(PayoutProjectionHealthSerializer(payload).data)

    @action(methods=["post"], detail=False, url_path="project-outbox")
    def project_outbox(self, request):
        serializer = PayoutProjectionRunSerializer(data=request.data or {})
        serializer.is_valid(raise_exception=True)
        result = DomainEventService().dispatch_pending_batch(batch_size=serializer.validated_data["batch_size"])
        AuditService.log_admin_action(
            request=request,
            action="payouts.project_outbox",
            target_type="outbox_batch",
            target_id="payouts_project_outbox",
            context={"input": serializer.validated_data, "result": result},
        )
        return Response(result, status=status.HTTP_202_ACCEPTED)

    @action(methods=["get"], detail=False, url_path="risk-holds")
    def risk_holds(self, request):
        queryset = (
            scope_balance_entries_for_user(BalanceEntry.objects.all(), request.user)
            .select_related("wallet", "wallet__trainer", "wallet__trainer__user")
            .filter(entry_type=BalanceEntry.EntryType.RISK_HOLD, source_type="payment_dispute_hold")
            .order_by("-created_at")
        )
        status_filter = (request.query_params.get("status") or "").strip()
        trainer_filter = (request.query_params.get("trainer_id") or "").strip()
        payment_filter = (request.query_params.get("payment_id") or "").strip()
        limit = min(int(request.query_params.get("limit") or 100), 500)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if trainer_filter:
            queryset = queryset.filter(Q(wallet__trainer__user_id=trainer_filter) | Q(wallet__trainer_id=trainer_filter))
        if payment_filter:
            queryset = queryset.filter(source_id=payment_filter)
        return Response(PayoutRiskHoldSerializer(queryset[:limit], many=True).data)

    @action(methods=["get"], detail=False, url_path="risk-holds/summary")
    def risk_holds_summary(self, request):
        limit = min(int(request.query_params.get("limit") or 50), 500)
        payload = PayoutService.build_risk_hold_report(limit=limit)
        return Response(PayoutRiskHoldReportSerializer(payload).data)

    @action(methods=["post"], detail=False, url_path="risk-holds/release")
    def release_risk_hold(self, request):
        serializer = ManualPaymentHoldReleaseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payment = scope_payments_for_user(Payment.objects.all(), request.user).get(id=serializer.validated_data["payment_id"])
        reason = serializer.validated_data.get("reason") or "manual_ops_release"
        result = PayoutService.release_payment_hold(payment=payment, reason=reason)
        AuditService.log_admin_action(
            request=request,
            action="payout_risk_hold.release",
            target_type="payment",
            target_id=str(payment.id),
            reason=reason,
            context={"result": result},
        )
        return Response(result, status=status.HTTP_202_ACCEPTED)

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
        AuditService.log_admin_action(
            request=request,
            action="payouts.reconciliation_repair",
            target_type="payout_reconciliation",
            target_id="repair",
            context={"input": serializer.validated_data, "result": payload},
        )
        return Response(payload)
