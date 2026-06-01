from __future__ import annotations

from typing import Any

from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.models import update_last_login
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import AccountProfile, AccountRoleAssignment, AccountSettings
from apps.accounts.selectors import get_account_payload

User = get_user_model()


def _token_payload_for_user(user) -> dict[str, str]:
    refresh = RefreshToken.for_user(user)
    return {'access_token': str(refresh.access_token), 'refresh_token': str(refresh)}


def _wrap_auth_payload(user) -> dict[str, Any]:
    return {'user': get_account_payload(user), **_token_payload_for_user(user)}


def _resolved_full_name(
    *,
    normalized_email: str,
    full_name: str = '',
    first_name: str = '',
    last_name: str = '',
) -> str:
    value = (full_name or '').strip()
    if value:
        return value

    pieces = [piece.strip() for piece in [first_name, last_name] if (piece or '').strip()]
    if pieces:
        return ' '.join(pieces)

    return normalized_email.split('@', 1)[0]


def _assign_role(*, user, role: str, is_active: bool) -> None:
    AccountRoleAssignment.objects.get_or_create(
        user=user,
        role=role,
        defaults={'is_active': is_active},
    )


def register_user(
    *,
    email: str,
    password: str,
    full_name: str = '',
    first_name: str = '',
    last_name: str = '',
    role: str = 'user',
    referral_invite_id: str | None = None,
    referral_code: str = '',
    click_session_key: str = '',
) -> dict[str, Any]:
    normalized_email = email.strip().lower()
    resolved_name = _resolved_full_name(
        normalized_email=normalized_email,
        full_name=full_name,
        first_name=first_name,
        last_name=last_name,
    )

    try:
        if User.objects.filter(email=normalized_email).exists():
            raise ValidationError({'email': 'User with this email already exists'})

        user_role = User.Roles.TRAINER if role == AccountRoleAssignment.ROLE_TRAINER else User.Roles.CUSTOMER
        user = User.objects.create_user(
            email=normalized_email,
            password=password,
            first_name=(first_name or resolved_name).strip()[:150],
            last_name=(last_name or '').strip()[:150],
            role=user_role,
        )
        AccountProfile.objects.create(user=user, full_name=resolved_name, display_name=resolved_name)
        AccountSettings.objects.create(user=user)

        from apps.referrals.services.integration import ReferralIntegrationService

        ReferralIntegrationService.bind_signup_from_request(
            referred_user=user,
            invite_id=referral_invite_id,
            referral_code=referral_code,
            click_session_key=click_session_key,
        )

        _assign_role(
            user=user,
            role=AccountRoleAssignment.ROLE_USER,
            is_active=role != AccountRoleAssignment.ROLE_TRAINER,
        )
        if role == AccountRoleAssignment.ROLE_TRAINER:
            _assign_role(user=user, role=AccountRoleAssignment.ROLE_TRAINER, is_active=True)

        return _wrap_auth_payload(user)
    except RuntimeError:
        return {'user': {'email': normalized_email, 'full_name': resolved_name, 'display_name': resolved_name}}


def login_user(*, email: str, password: str) -> dict[str, Any]:
    normalized_email = email.strip().lower()
    user = authenticate(email=normalized_email, password=password)
    if user is None:
        user = authenticate(username=normalized_email, password=password)
    if user is None:
        raise AuthenticationFailed('Invalid credentials')
    update_last_login(None, user)
    return _wrap_auth_payload(user)


def refresh_tokens(*, refresh_token: str) -> dict[str, str]:
    try:
        refresh = RefreshToken(refresh_token)
    except Exception as exc:
        raise AuthenticationFailed('Invalid refresh token') from exc
    return {'access_token': str(refresh.access_token), 'refresh_token': str(refresh)}


def logout_user(*, refresh_token: str) -> dict[str, str]:
    try:
        token = RefreshToken(refresh_token)
        token.blacklist()
    except Exception as exc:
        raise AuthenticationFailed('Invalid refresh token') from exc
    return {'status': 'logged_out'}


def current_session_payload(*, user) -> dict[str, Any]:
    if not user or not user.is_authenticated:
        return {'is_authenticated': False, 'user': None}
    return {'is_authenticated': True, 'user': get_account_payload(user)}
