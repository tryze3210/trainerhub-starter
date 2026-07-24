from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.tenancy.api.serializers import TenantContextSerializer, TenantSwitchSerializer, ActiveTenantSerializer, MembershipSerializer
from apps.tenancy.services import TenancyService


class TenantContextView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    service = TenancyService()

    def get(self, request):
        payload = self.service.get_context()
        return Response(TenantContextSerializer(payload).data)


class TenantMembershipListView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    service = TenancyService()

    def get(self, request):
        payload = self.service.get_context()
        return Response(MembershipSerializer(payload['memberships'], many=True).data)


class TenantSwitchView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    service = TenancyService()

    def post(self, request):
        serializer = TenantSwitchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = self.service.switch_active_tenant(serializer.validated_data['tenant_code'])
        return Response({
            'active_tenant': ActiveTenantSerializer(payload['active_tenant']).data,
            'status': payload['status'],
        }, status=status.HTTP_200_OK)
