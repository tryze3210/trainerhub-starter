from __future__ import annotations

from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from apps.subscriptions.api.lifecycle_serializers import (
    SubscriptionLifecycleActionSerializer,
    SubscriptionLifecycleReconcileSerializer,
    SubscriptionLifecycleSummaryQuerySerializer,
)
from apps.subscriptions.api.serializers import (
    AdminSubscriptionListQuerySerializer,
    SubscriptionActionSerializer,
    SubscriptionSerializer,
)
from apps.subscriptions.lifecycle import SubscriptionLifecycleService
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
        if self.request.user.is_staff:
            return Subscription.objects.select_related('plan', 'source_order', 'user').prefetch_related(
                'granted_entitlements', 'source_order__payments'
            ).order_by('-created_at')
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
        payload = get_user_subscription_center(request.user, days=days)
        payload['lifecycle'] = SubscriptionLifecycleService.get_lifecycle_summary(user=request.user, days=days)
        return Response(payload)

    @action(detail=False, methods=['get'], url_path='lifecycle-policy')
    def lifecycle_policy(self, request):
        return Response(SubscriptionLifecycleService.status_policy())

    @action(detail=False, methods=['get'], url_path='lifecycle-summary')
    def lifecycle_summary(self, request):
        query = SubscriptionLifecycleSummaryQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        return Response(
            SubscriptionLifecycleService.get_lifecycle_summary(
                user=request.user,
                days=query.validated_data['days'],
            )
        )

    @action(detail=True, methods=['get'], url_path='renewal-projection')
    def renewal_projection(self, request, pk=None):
        subscription = self.get_object()
        return Response(SubscriptionLifecycleService.project_renewal(subscription))

    @action(detail=True, methods=['post'], url_path='sync-entitlements')
    def sync_entitlements(self, request, pk=None):
        subscription = self.get_object()
        serializer = SubscriptionLifecycleActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = SubscriptionLifecycleService.sync_subscription_entitlements(
            subscription=subscription,
            actor=request.user,
            request=request,
            reason=serializer.validated_data.get('reason') or 'customer_subscription_entitlement_sync',
        )
        return Response(result.as_dict())

    @action(detail=True, methods=['post'], url_path='cancel')
    def cancel(self, request, pk=None):
        subscription = self.get_object()
        serializer = SubscriptionActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = SubscriptionLifecycleService.cancel_subscription(
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
            result = SubscriptionLifecycleService.resume_subscription(
                subscription=subscription,
                actor=request.user,
                request=request,
                reason='customer_self_service_resume',
            )
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(SubscriptionSerializer(result).data)

    @action(detail=True, methods=['post'], url_path='resume')
    def resume(self, request, pk=None):
        subscription = self.get_object()
        serializer = SubscriptionLifecycleActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            result = SubscriptionLifecycleService.resume_subscription(
                subscription=subscription,
                actor=request.user,
                request=request,
                reason=serializer.validated_data.get('reason') or 'subscription_resumed',
            )
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(SubscriptionSerializer(result).data)

    @action(detail=False, methods=['get'], permission_classes=[IsAdminUser], url_path='admin/overview')
    def admin_overview(self, request):
        days = int(request.query_params.get('days', 30))
        days = max(1, min(days, 365))
        payload = get_admin_subscription_overview(days=days)
        payload['lifecycle'] = SubscriptionLifecycleService.get_lifecycle_summary(days=days)
        return Response(payload)

    @action(detail=False, methods=['get'], permission_classes=[IsAdminUser], url_path='admin/items')
    def admin_items(self, request):
        query = AdminSubscriptionListQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        items = list_admin_subscriptions(**query.validated_data)
        return Response([serialize_subscription(item) for item in items])

    @action(detail=False, methods=['get'], permission_classes=[IsAdminUser], url_path='admin/lifecycle-policy')
    def admin_lifecycle_policy(self, request):
        return Response(SubscriptionLifecycleService.status_policy())

    @action(detail=False, methods=['get'], permission_classes=[IsAdminUser], url_path='admin/lifecycle-summary')
    def admin_lifecycle_summary(self, request):
        query = SubscriptionLifecycleSummaryQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        return Response(SubscriptionLifecycleService.get_lifecycle_summary(days=query.validated_data['days']))

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
        if request.data.get('sync_entitlements', True):
            SubscriptionLifecycleService.sync_subscription_entitlements(
                subscription=result,
                actor=request.user,
                request=request,
                reason='admin_mark_past_due',
            )
        return Response(SubscriptionSerializer(result).data)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser], url_path='admin/sync-entitlements')
    def admin_sync_entitlements(self, request, pk=None):
        subscription = Subscription.objects.get(pk=pk)
        serializer = SubscriptionLifecycleActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = SubscriptionLifecycleService.sync_subscription_entitlements(
            subscription=subscription,
            actor=request.user,
            request=request,
            reason=serializer.validated_data.get('reason') or 'admin_subscription_entitlement_sync',
        )
        return Response(result.as_dict())

    @action(detail=False, methods=['post'], permission_classes=[IsAdminUser], url_path='admin/reconcile-entitlements')
    def admin_reconcile_entitlements(self, request):
        serializer = SubscriptionLifecycleReconcileSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = SubscriptionLifecycleService.reconcile_subscriptions(
            limit=serializer.validated_data.get('limit', 100),
            subscription_id=serializer.validated_data.get('subscription_id'),
            actor=request.user,
            request=request,
        )
        return Response(payload)

    @action(detail=False, methods=['post'], permission_classes=[IsAdminUser], url_path='admin/expire-due')
    def admin_expire_due(self, request):
        count = SubscriptionService.expire_due_subscriptions(actor=request.user, request=request)
        reconcile = SubscriptionLifecycleService.reconcile_subscriptions(
            limit=100,
            actor=request.user,
            request=request,
        )
        return Response({'expired_count': count, 'entitlement_reconciliation': reconcile})
