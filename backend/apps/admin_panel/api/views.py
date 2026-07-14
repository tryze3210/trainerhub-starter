from datetime import datetime, timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from apps.audit.services import AuditService
from apps.common.api.permissions import IsAdminUserRole
from apps.admin_panel.api.serializers import ModerationQueueItemSerializer, PaymentAdminSerializer, PayoutAdminSerializer
from apps.legal_compliance.services.eligibility import PayoutEligibilityService
from apps.payments.selectors import list_all_payments
from apps.payouts.models import PayoutRequest
from apps.payouts.selectors import list_all_payout_requests
from apps.payouts.services import PayoutService


class ModerationAdminViewSet(viewsets.ViewSet):
    permission_classes = [IsAdminUserRole]

    def list(self, request):
        items = [{
            'id': 'mod_1', 'entity_type': 'video', 'entity_id': 'video_12', 'status': 'pending', 'reason': '', 'submitted_at': datetime.now(timezone.utc),
        }]
        return Response(ModerationQueueItemSerializer(items, many=True).data)

    @action(methods=['post'], detail=True, url_path='approve')
    def approve(self, request, pk=None):
        return Response({'id': pk, 'status': 'approved'})

    @action(methods=['post'], detail=True, url_path='reject')
    def reject(self, request, pk=None):
        return Response({'id': pk, 'status': 'rejected'})


class PaymentAdminViewSet(viewsets.ViewSet):
    permission_classes = [IsAdminUserRole]

    def list(self, request):
        items = [{
            'id': str(p.id),
            'payer_id': str(p.user_id),
            'order_id': p.order_reference,
            'provider': p.provider,
            'provider_payment_id': p.provider_payment_id,
            'status': p.status,
            'gross_amount': str(p.gross_amount),
            'platform_fee': str(p.platform_fee_amount),
            'trainer_amount': str(p.trainer_net_amount),
            'created_at': p.created_at,
            'paid_at': p.paid_at,
        } for p in list_all_payments()[:100]]
        return Response(PaymentAdminSerializer(items, many=True).data)

    def retrieve(self, request, pk=None):
        payment = list_all_payments().get(pk=pk)
        item = {
            'id': str(payment.id),
            'payer_id': str(payment.user_id),
            'order_id': payment.order_reference,
            'provider': payment.provider,
            'provider_payment_id': payment.provider_payment_id,
            'status': payment.status,
            'gross_amount': str(payment.gross_amount),
            'platform_fee': str(payment.platform_fee_amount),
            'trainer_amount': str(payment.trainer_net_amount),
            'created_at': payment.created_at,
            'paid_at': payment.paid_at,
        }
        return Response(PaymentAdminSerializer(item).data)

    @action(methods=['post'], detail=True, url_path='refund')
    def refund(self, request, pk=None):
        return Response({'id': pk, 'status': 'refund_pending_manual_integration'})


class PayoutAdminViewSet(viewsets.ViewSet):
    permission_classes = [IsAdminUserRole]

    @staticmethod
    def _eligibility_payload(payout: PayoutRequest) -> dict:
        result = PayoutEligibilityService.evaluate_for_trainer(payout.trainer.user)
        return {
            "is_eligible": result.is_eligible,
            "block_reason": result.block_reason,
            "has_active_agreement": result.has_active_agreement,
            "has_verified_payout_profile": result.has_verified_payout_profile,
            "kyc_status": result.kyc_status,
        }

    @staticmethod
    def _transition_response(*, request, payout: PayoutRequest, action: str):
        try:
            updated = PayoutService.transition(payout=payout, action=action, actor=request.user, request=request)
        except ValidationError as exc:
            detail = getattr(exc, "detail", {})
            if "block_reason" in detail:
                AuditService.log(
                    actor=request.user,
                    request=request,
                    event_type="payout.eligibility_blocked",
                    entity_type="payout_request",
                    entity_id=str(payout.id),
                    context={
                        "action": action,
                        "payout_id": str(payout.id),
                        "trainer_id": str(payout.trainer.user_id),
                        "amount": str(payout.amount),
                        "status": PayoutService._canonical_status(payout.status),
                        "block_reason": str(detail.get("block_reason", "")),
                        "surface": "legacy_admin_panel",
                    },
                )
            raise
        return Response({'id': str(updated.id), 'status': PayoutService._canonical_status(updated.status)})

    def list(self, request):
        items = [{
            'id': str(p.id),
            'trainer_id': str(p.trainer.user_id),
            'amount': str(p.amount),
            'currency': p.currency,
            'status': PayoutService._canonical_status(p.status),
            'destination_masked': p.destination_masked,
            'payout_eligibility': self._eligibility_payload(p),
            'requested_at': p.requested_at,
            'approved_at': p.approved_at,
            'processed_at': p.processed_at,
        } for p in list_all_payout_requests().select_related("trainer__user")[:100]]
        return Response(PayoutAdminSerializer(items, many=True).data)

    @action(methods=['post'], detail=True, url_path='approve')
    def approve(self, request, pk=None):
        payout = PayoutRequest.objects.get(pk=pk)
        return self._transition_response(request=request, payout=payout, action="approve")

    @action(methods=['post'], detail=True, url_path='process')
    def process(self, request, pk=None):
        payout = PayoutRequest.objects.get(pk=pk)
        return self._transition_response(request=request, payout=payout, action="processing")

    @action(methods=['post'], detail=True, url_path='mark-paid')
    def mark_paid(self, request, pk=None):
        payout = PayoutRequest.objects.get(pk=pk)
        return self._transition_response(request=request, payout=payout, action="paid")
