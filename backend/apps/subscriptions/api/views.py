from __future__ import annotations

from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from apps.subscriptions.api.serializers import (
    AdminSubscriptionListQuerySerializer,
    SubscriptionActionSerializer,
    SubscriptionSerializer,
)
from apps.subscriptions.models import Subscription
from apps.subscriptions.selectors import (
    get_admin_subscription_overview,
    get_user_subscription_center,
    list_admin_subscriptions,
    list_user_subscriptions,
    serialize_subscription,
)
from apps.subscriptions.services import SubscriptionService


class SubscriptionViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return list_user_subscriptions(self.request.user)

    def get_object(self):
        subscription = super().get_object()
        if self.request.user.is_staff or subscription.user_id == self.request.user.id:
            return subscription
        self.permission_denied(self.request, message='You do not have access to this subscription.')
        return subscription

    @action(detail=False, methods=['get'], url_path='center')
    def center(self, request):
        days = int(request.query_params.get('days', 30))
        days = max(1, min(days, 365))
        return Response(get_user_subscription_center(request.user, days=days))

    @action(detail=True, methods=['post'], url_path='cancel')
    def cancel(self, request, pk=None):
        subscription = self.get_object()
        serializer = SubscriptionActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = SubscriptionService.cancel_subscription(
            subscription=subscription,
            actor=request.user,
            reason=serializer.validated_data.get('reason', ''),
            request=request,
        )
        return Response(SubscriptionSerializer(result).data)

    @action(detail=True, methods=['post'], url_path='reactivate')
    def reactivate(self, request, pk=None):
        subscription = self.get_object()
        try:
            result = SubscriptionService.reactivate_subscription(
                subscription=subscription,
                actor=request.user,
                request=request,
            )
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(SubscriptionSerializer(result).data)

    @action(detail=False, methods=['get'], permission_classes=[IsAdminUser], url_path='admin/overview')
    def admin_overview(self, request):
        days = int(request.query_params.get('days', 30))
        days = max(1, min(days, 365))
        return Response(get_admin_subscription_overview(days=days))

    @action(detail=False, methods=['get'], permission_classes=[IsAdminUser], url_path='admin/items')
    def admin_items(self, request):
        query = AdminSubscriptionListQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        items = list_admin_subscriptions(**query.validated_data)
        return Response([serialize_subscription(item) for item in items])

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser], url_path='admin/mark-past-due')
    def admin_mark_past_due(self, request, pk=None):
        subscription = Subscription.objects.get(pk=pk)
        serializer = SubscriptionActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = SubscriptionService.mark_past_due(
            subscription=subscription,
            actor=request.user,
            reason=serializer.validated_data.get('reason', ''),
            request=request,
        )
        return Response(SubscriptionSerializer(result).data)

    @action(detail=False, methods=['post'], permission_classes=[IsAdminUser], url_path='admin/expire-due')
    def admin_expire_due(self, request):
        count = SubscriptionService.expire_due_subscriptions(actor=request.user, request=request)
        return Response({'expired_count': count})
