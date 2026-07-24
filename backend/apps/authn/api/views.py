from django.conf import settings
from django.middleware.csrf import get_token
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.authn import services
from apps.authn.authentication import enforce_csrf
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


def _prepare_auth_response(request, response: Response, payload: dict) -> Response:
    get_token(request)
    return _set_auth_cookies(response, payload)


def _public_auth_payload(payload: dict) -> dict:
    return {'user': payload.get('user')}


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


def _refresh_token_from_request(request) -> tuple[str, bool]:
    explicit_token = request.data.get('refresh_token') or request.data.get('refresh')
    if explicit_token:
        return explicit_token, False
    return request.COOKIES.get(settings.AUTH_REFRESH_COOKIE_NAME, ''), True


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
        return _prepare_auth_response(request, Response(_public_auth_payload(payload), status=201), payload)


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
        return _prepare_auth_response(request, Response(_public_auth_payload(payload)), payload)


class RefreshView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'auth_refresh'

    def post(self, request):
        request_data = request.data.copy()
        refresh_token, from_cookie = _refresh_token_from_request(request)
        if from_cookie and refresh_token:
            enforce_csrf(request)
        request_data['refresh_token'] = refresh_token
        serializer = RefreshSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)
        if not serializer.validated_data.get('refresh_token'):
            return _clear_auth_cookies(
                Response({'detail': 'Refresh token is required'}, status=401)
            )
        payload = services.refresh_tokens(**serializer.validated_data)
        TokenPairSerializer(data=payload).is_valid(raise_exception=True)
        return _prepare_auth_response(request, Response({'status': 'refreshed'}), payload)


class LogoutView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'auth_logout'

    def post(self, request):
        request_data = request.data.copy()
        refresh_token, from_cookie = _refresh_token_from_request(request)
        if from_cookie and refresh_token:
            enforce_csrf(request)
        request_data['refresh_token'] = refresh_token
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
