from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.authn import services
from apps.authn.api.serializers import (
    AuthUserSerializer,
    LoginSerializer,
    LogoutSerializer,
    RefreshSerializer,
    RegisterSerializer,
    SessionSerializer,
    TokenPairSerializer,
)


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = services.register_user(**serializer.validated_data)
        return Response(AuthUserSerializer(payload).data, status=201)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = services.login_user(**serializer.validated_data)
        return Response(AuthUserSerializer(payload).data)


class RefreshView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RefreshSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = services.refresh_tokens(**serializer.validated_data)
        return Response(TokenPairSerializer(payload).data)


class LogoutView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = services.logout_user(**serializer.validated_data)
        return Response(payload)


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        payload = services.current_session_payload(user=request.user)
        return Response(SessionSerializer(payload).data)
