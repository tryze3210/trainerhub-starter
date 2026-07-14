from django.conf import settings
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.authn import services
from apps.authn.api.serializers import (
    LoginSerializer,
    LogoutSerializer,
    RefreshSerializer,
    RegisterSerializer,
    SessionSerializer,
    TokenPairSerializer,
)


def _request_meta(request) -> dict[str, str]:
    forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR', '')
    remote_addr = forwarded_for.split(',', 1)[0].strip() or request.META.get('REMOTE_ADDR', '')
    return {
        'ip': remote_addr.replace('\n', ' ').replace('\r', ' ')[:64],
        'user_agent': (
            request.META.get('HTTP_USER_AGENT', '')
            .replace('\n', ' ')
            .replace('\r', ' ')[:255]
        ),
    }


def _set_auth_cookies(response: Response, payload: dict) -> Response:
    access_token = payload.get('access_token')
    refresh_token = payload.get('refresh_token')
    if access_token:
        response.set_cookie(
            settings.AUTH_ACCESS_COOKIE_NAME,
            access_token,
            max_age=int(settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds()),
            httponly=True,
            secure=settings.AUTH_COOKIE_SECURE,
            samesite=settings.AUTH_COOKIE_SAMESITE,
            path=settings.AUTH_COOKIE_PATH,
        )
    if refresh_token:
        response.set_cookie(
            settings.AUTH_REFRESH_COOKIE_NAME,
            refresh_token,
            max_age=int(settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds()),
            httponly=True,
            secure=settings.AUTH_COOKIE_SECURE,
            samesite=settings.AUTH_COOKIE_SAMESITE,
            path=settings.AUTH_COOKIE_PATH,
        )
    return response


def _clear_auth_cookies(response: Response) -> Response:
    response.delete_cookie(
        settings.AUTH_ACCESS_COOKIE_NAME,
        path=settings.AUTH_COOKIE_PATH,
        samesite=settings.AUTH_COOKIE_SAMESITE,
    )
    response.delete_cookie(
        settings.AUTH_REFRESH_COOKIE_NAME,
        path=settings.AUTH_COOKIE_PATH,
        samesite=settings.AUTH_COOKIE_SAMESITE,
    )
    return response


class RegisterView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'auth_register'

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = services.register_user(
            **serializer.validated_data,
            request_meta=_request_meta(request),
        )
        return _set_auth_cookies(Response(payload, status=201), payload)


class LoginView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'auth_login'

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = services.login_user(
            **serializer.validated_data,
            request_meta=_request_meta(request),
        )
        return _set_auth_cookies(Response(payload), payload)


class RefreshView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'auth_refresh'

    def post(self, request):
        request_data = request.data.copy()
        request_data['refresh_token'] = (
            request_data.get('refresh_token')
            or request.COOKIES.get(settings.AUTH_REFRESH_COOKIE_NAME, '')
        )
        serializer = RefreshSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)
        if not serializer.validated_data.get('refresh_token'):
            return _clear_auth_cookies(
                Response({'detail': 'Refresh token is required'}, status=401)
            )
        payload = services.refresh_tokens(**serializer.validated_data)
        response_payload = TokenPairSerializer(payload).data
        return _set_auth_cookies(Response(response_payload), response_payload)


class LogoutView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        request_data = request.data.copy()
        request_data['refresh_token'] = (
            request_data.get('refresh_token')
            or request.COOKIES.get(settings.AUTH_REFRESH_COOKIE_NAME, '')
        )
        serializer = LogoutSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)
        if serializer.validated_data.get('refresh_token'):
            payload = services.logout_user(
                **serializer.validated_data,
                request_meta=_request_meta(request),
            )
        else:
            payload = {'status': 'logged_out'}
        return _clear_auth_cookies(Response(payload))


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        payload = services.current_session_payload(user=request.user)
        return Response(SessionSerializer(payload).data)
