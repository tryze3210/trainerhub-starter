from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from apps.payouts.api.serializers import TrainerBalanceSerializer, PayoutRequestSerializer, CreatePayoutRequestSerializer
from apps.payouts.selectors import get_balance_for_trainer, list_payout_requests_for_trainer
from apps.payouts.services import PayoutService


class MyPayoutViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = PayoutRequestSerializer

    def _trainer_id(self):
        return self.request.user.profile.trainer_id  # align to your real trainer profile relation

    def get_queryset(self):
        return list_payout_requests_for_trainer(self._trainer_id())

    @action(methods=['get'], detail=False, url_path='balance')
    def balance(self, request):
        balance = get_balance_for_trainer(self._trainer_id())
        if not balance:
            balance = PayoutService.get_or_create_balance(trainer_id=self._trainer_id())
        return Response(TrainerBalanceSerializer(balance).data)

    @action(methods=['post'], detail=False, url_path='request')
    def request_payout(self, request):
        serializer = CreatePayoutRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payout = PayoutService.request_payout(
            trainer_id=self._trainer_id(),
            amount=serializer.validated_data['amount'],
            destination_masked=serializer.validated_data['destination_masked'],
            request=request,
        )
        return Response(PayoutRequestSerializer(payout).data, status=status.HTTP_201_CREATED)
