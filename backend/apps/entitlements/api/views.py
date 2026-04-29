from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.entitlements.api.serializers import AccessCheckRequestSerializer, AccessDecisionSerializer, EntitlementSerializer
from apps.entitlements.models import Entitlement
from apps.entitlements.selectors import EntitlementAccessCenterSelector
from apps.entitlements.services import EntitlementService


class EntitlementViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = EntitlementSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        EntitlementService.expire_due_entitlements()
        return (
            Entitlement.objects.filter(user=self.request.user)
            .select_related('source_order', 'source_subscription')
            .order_by('-created_at')
        )

    @action(detail=False, methods=['get'], url_path='access-center')
    def access_center(self, request):
        days = request.query_params.get('days') or 30
        payload = EntitlementAccessCenterSelector().build(user=request.user, days=int(days))
        return Response(payload, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='check-access')
    def check_access(self, request):
        serializer = AccessCheckRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = EntitlementAccessCenterSelector().check(user=request.user, **serializer.validated_data)
        return Response(AccessDecisionSerializer(payload).data, status=status.HTTP_200_OK)
