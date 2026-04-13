from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.billing.api.serializers import (
    CreatePayoutBatchSerializer,
    LedgerEntrySerializer,
    PayoutBatchSerializer,
    TrainerRevenuePolicySerializer,
    TransitionPayoutBatchSerializer,
)
from apps.billing.models import LedgerEntry, PayoutBatch, TrainerRevenuePolicy
from apps.billing.services.payouts import PayoutService


class IsAdminOrTrainerOwner(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated


class TrainerRevenuePolicyAdminViewSet(viewsets.ModelViewSet):
    queryset = TrainerRevenuePolicy.objects.select_related("trainer").all()
    serializer_class = TrainerRevenuePolicySerializer
    permission_classes = [permissions.IsAdminUser]


class TrainerLedgerViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = LedgerEntrySerializer
    permission_classes = [IsAdminOrTrainerOwner]

    def get_queryset(self):
        queryset = LedgerEntry.objects.select_related(
            "trainer",
            "user",
            "order",
            "payment",
            "refund",
            "subscription",
            "subscription_cycle",
            "entitlement",
        )
        trainer_id = self.request.query_params.get("trainer_id")
        if self.request.user.is_staff and trainer_id:
            return queryset.filter(trainer_id=trainer_id)
        return queryset.filter(trainer__user=self.request.user)


class PayoutBatchAdminViewSet(viewsets.ModelViewSet):
    queryset = PayoutBatch.objects.select_related("trainer").prefetch_related("items__ledger_entry")
    serializer_class = PayoutBatchSerializer
    permission_classes = [permissions.IsAdminUser]

    @action(detail=False, methods=["post"], url_path="create-batch")
    def create_batch(self, request):
        serializer = CreatePayoutBatchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        trainer_model = PayoutBatch._meta.get_field("trainer").remote_field.model
        trainer = trainer_model.objects.get(id=serializer.validated_data["trainer_id"])
        batch = PayoutService.create_batch(
            trainer=trainer,
            amount=serializer.validated_data.get("amount"),
            currency=serializer.validated_data.get("currency", "RUB"),
        )
        return Response(PayoutBatchSerializer(batch, context={"request": request}).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="mark-processing")
    def mark_processing(self, request, pk=None):
        batch = self.get_object()
        serializer = TransitionPayoutBatchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        batch = PayoutService.mark_processing(batch=batch, payout_reference=serializer.validated_data["payout_reference"])
        return Response(PayoutBatchSerializer(batch, context={"request": request}).data)

    @action(detail=True, methods=["post"], url_path="mark-paid")
    def mark_paid(self, request, pk=None):
        batch = self.get_object()
        batch = PayoutService.mark_paid(batch=batch)
        return Response(PayoutBatchSerializer(batch, context={"request": request}).data)

    @action(detail=True, methods=["post"], url_path="cancel")
    def cancel(self, request, pk=None):
        batch = self.get_object()
        serializer = TransitionPayoutBatchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        batch = PayoutService.cancel_batch(batch=batch, reason=serializer.validated_data["reason"])
        return Response(PayoutBatchSerializer(batch, context={"request": request}).data)
