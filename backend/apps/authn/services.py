from __future__ import annotations

from typing import Any

from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.models import update_last_login
from django.db import transaction
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import AccountProfile, AccountRoleAssignment, AccountSettings
from apps.accounts.selectors import get_account_payload

User = get_user_model()


def _token_payload_for_user(user) -> dict[str, str]:
    refresh = RefreshToken.for_user(user)
    return {
        'access_token': str(refresh.access_token),
        'refresh_token': str(refresh),
    }


@transaction.atomic
def register_user(*, email: str, password: str, full_name: str) -> dict[str, Any]:
    normalized_email = email.strip().lower()
    if User.objects.filter(email=normalized_email).exists():
        raise ValidationError({'email': 'User with this email already exists'})
    user = User.objects.create_user(
        username=normalized_email,
        email=normalized_email,
        password=password,
        first_name=full_name,
    )
    AccountProfile.objects.create(user=user, full_name=full_name, display_name=full_name)
    AccountSettings.objects.create(user=user)
    AccountRoleAssignment.objects.create(user=user, role=AccountRoleAssignment.ROLE_USER, is_active=True)
    payload = get_account_payload(user)
    payload.update(_token_payload_for_user(user))
    return payload


def login_user(*, email: str, password: str) -> dict[str, Any]:
    normalized_email = email.strip().lower()
    user = authenticate(username=normalized_email, password=password)
    if user is None:
        raise AuthenticationFailed('Invalid credentials')
    update_last_login(None, user)
    payload = get_account_payload(user)
    payload.update(_token_payload_for_user(user))
    return payload


def refresh_tokens(*, refresh_token: str) -> dict[str, str]:
    try:
        refresh = RefreshToken(refresh_token)
    except Exception as exc:  # pragma: no cover - provider validation
        raise AuthenticationFailed('Invalid refresh token') from exc
    return {
        'access_token': str(refresh.access_token),
        'refresh_token': str(refresh),
    }


def logout_user(*, refresh_token: str) -> dict[str, str]:
    try:
        token = RefreshToken(refresh_token)
        token.blacklist()
    except Exception as exc:  # pragma: no cover - provider validation
        raise AuthenticationFailed('Invalid refresh token') from exc
    return {'status': 'logged_out'}


def current_session_payload(*, user) -> dict[str, Any]:
    if not user or not user.is_authenticated:
        return {'is_authenticated': False, 'user': None}
    return {
        'is_authenticated': True,
        'user': get_account_payload(user),
    }
