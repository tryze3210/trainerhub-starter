from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts import services
from apps.accounts.api.serializers import (
    CabinetSerializer,
    ProfileSerializer,
    RoleSwitchResultSerializer,
    SettingsSerializer,
    SwitchRoleSerializer,
)


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        payload = services.get_profile(user=request.user)
        return Response(ProfileSerializer(payload).data)

    def patch(self, request):
        serializer = ProfileSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        payload = services.update_profile(user=request.user, payload=serializer.validated_data)
        return Response(ProfileSerializer(payload).data)


class SettingsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        payload = services.get_settings(user=request.user)
        return Response(SettingsSerializer(payload).data)

    def patch(self, request):
        serializer = SettingsSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        payload = services.update_settings(user=request.user, payload=serializer.validated_data)
        return Response(SettingsSerializer(payload).data)


class RoleSwitchView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SwitchRoleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = services.switch_role(user=request.user, role=serializer.validated_data['role'])
        return Response(RoleSwitchResultSerializer(payload).data)


class CabinetView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        payload = services.get_cabinet(user=request.user)
        return Response(CabinetSerializer(payload).data)


AccountProfileView = ProfileView
AccountSettingsView = SettingsView
SwitchRoleView = RoleSwitchView
