from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated
from apps.subscriptions.api.serializers import SubscriptionSerializer
from apps.subscriptions.models import Subscription


class SubscriptionViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Subscription.objects.filter(user=self.request.user).select_related('plan').order_by('-created_at')
