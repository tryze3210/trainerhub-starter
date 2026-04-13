from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from apps.billing.api.serializers import CreateCheckoutSessionSerializer, CheckoutSessionSerializer
from apps.billing.selectors import list_checkout_sessions_for_user
from apps.billing.services import CheckoutService


class CheckoutSessionViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = CheckoutSessionSerializer

    def get_queryset(self):
        return list_checkout_sessions_for_user(self.request.user)

    @action(methods=['post'], detail=False, url_path='create')
    def create_session(self, request):
        serializer = CreateCheckoutSessionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if serializer.validated_data['checkout_type'] == 'subscription':
            checkout, checkout_url = CheckoutService.create_subscription_checkout(
                user=request.user,
                plan_id=serializer.validated_data['target_id'],
                success_url=serializer.validated_data.get('success_url', ''),
                cancel_url=serializer.validated_data.get('cancel_url', ''),
                request=request,
            )
            return Response({'checkout_session': CheckoutSessionSerializer(checkout).data, 'checkout_url': checkout_url}, status=status.HTTP_201_CREATED)
        return Response({'detail': 'Unsupported checkout type.'}, status=status.HTTP_400_BAD_REQUEST)
