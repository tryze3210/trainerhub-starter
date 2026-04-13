from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated
from apps.entitlements.api.serializers import EntitlementSerializer
from apps.entitlements.models import Entitlement


class EntitlementViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = EntitlementSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Entitlement.objects.filter(user=self.request.user).order_by('-created_at')
