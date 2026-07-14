from __future__ import annotations

import logging
from typing import Any

from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.models import update_last_login
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import AccountProfile, AccountRoleAssignment, AccountSettings
from apps.accounts.selectors import get_account_payload
from apps.audit.services import AuditService

User = get_user_model()
logger = logging.getLogger('apps.authn')


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


def _safe_auth_meta(
    email: str,
    request_meta: dict[str, str] | None = None,
) -> dict[str, Any]:
    meta = request_meta or {}
    return {
        'email': email,
        'ip': meta.get('ip', ''),
        'user_agent': meta.get('user_agent', ''),
    }


def _audit_auth_event(*, event_type: str, entity_id: str, context: dict[str, Any]) -> None:
    try:
        AuditService.log(
            event_type=event_type,
            entity_type='user',
            entity_id=entity_id,
            context=context,
        )
    except Exception:
        logger.exception('auth.audit_failed event_type=%s entity_id=%s', event_type, entity_id)


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
    request_meta: dict[str, str] | None = None,
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

        user_role = (
            User.Roles.TRAINER
            if role == AccountRoleAssignment.ROLE_TRAINER
            else User.Roles.CUSTOMER
        )
        user = User.objects.create_user(
            email=normalized_email,
            password=password,
            first_name=(first_name or resolved_name).strip()[:150],
            last_name=(last_name or '').strip()[:150],
            role=user_role,
        )
        AccountProfile.objects.create(
            user=user,
            full_name=resolved_name,
            display_name=resolved_name,
        )
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

        _audit_auth_event(
            event_type='auth.register',
            entity_id=str(user.id),
            context={
                **_safe_auth_meta(normalized_email, request_meta),
                'status': 'success',
                'user_id': str(user.id),
                'role': role,
                'referral_invite_id': str(referral_invite_id or ''),
                'referral_code_present': bool(referral_code),
                'click_session_key_present': bool(click_session_key),
            },
        )
        return _wrap_auth_payload(user)
    except RuntimeError:
        return {
            'user': {
                'email': normalized_email,
                'full_name': resolved_name,
                'display_name': resolved_name,
            }
        }


def login_user(
    *,
    email: str,
    password: str,
    request_meta: dict[str, str] | None = None,
) -> dict[str, Any]:
    normalized_email = email.strip().lower()
    log_meta = _safe_auth_meta(normalized_email, request_meta)
    logger.info(
        'auth.login.attempt email=%s ip=%s user_agent=%s',
        log_meta['email'],
        log_meta['ip'],
        log_meta['user_agent'],
        extra=log_meta,
    )

    existing_user = (
        User.objects.filter(email__iexact=normalized_email)
        .only('id', 'email', 'is_active')
        .first()
    )
    if existing_user is None:
        logger.warning(
            'auth.login.failure reason=user_not_found email=%s ip=%s',
            log_meta['email'],
            log_meta['ip'],
            extra={**log_meta, 'reason': 'user_not_found'},
        )
        _audit_auth_event(
            event_type='auth.login_failed',
            entity_id=normalized_email[:64],
            context={**log_meta, 'reason': 'user_not_found'},
        )
        raise AuthenticationFailed('Invalid credentials')
    if not existing_user.is_active:
        logger.warning(
            'auth.login.failure reason=inactive_user email=%s user_id=%s ip=%s',
            log_meta['email'],
            existing_user.id,
            log_meta['ip'],
            extra={**log_meta, 'reason': 'inactive_user', 'user_id': str(existing_user.id)},
        )
        _audit_auth_event(
            event_type='auth.login_failed',
            entity_id=str(existing_user.id),
            context={**log_meta, 'reason': 'inactive_user', 'user_id': str(existing_user.id)},
        )
        raise AuthenticationFailed('Invalid credentials')

    user = authenticate(email=normalized_email, password=password)
    if user is None:
        user = authenticate(username=normalized_email, password=password)
    if user is None:
        logger.warning(
            'auth.login.failure reason=invalid_password email=%s user_id=%s ip=%s',
            log_meta['email'],
            existing_user.id,
            log_meta['ip'],
            extra={**log_meta, 'reason': 'invalid_password', 'user_id': str(existing_user.id)},
        )
        _audit_auth_event(
            event_type='auth.login_failed',
            entity_id=str(existing_user.id),
            context={**log_meta, 'reason': 'invalid_password', 'user_id': str(existing_user.id)},
        )
        raise AuthenticationFailed('Invalid credentials')
    update_last_login(None, user)
    logger.info(
        'auth.login.success email=%s user_id=%s role=%s ip=%s',
        log_meta['email'],
        user.id,
        getattr(user, 'role', ''),
        log_meta['ip'],
        extra={**log_meta, 'user_id': str(user.id), 'role': getattr(user, 'role', '')},
    )
    _audit_auth_event(
        event_type='auth.login',
        entity_id=str(user.id),
        context={**log_meta, 'status': 'success', 'user_id': str(user.id), 'role': getattr(user, 'role', '')},
    )
    return _wrap_auth_payload(user)


def refresh_tokens(*, refresh_token: str) -> dict[str, str]:
    try:
        refresh = RefreshToken(refresh_token)
    except Exception as exc:
        raise AuthenticationFailed('Invalid refresh token') from exc
    return {'access_token': str(refresh.access_token), 'refresh_token': str(refresh)}


def logout_user(*, refresh_token: str, request_meta: dict[str, str] | None = None) -> dict[str, str]:
    log_meta = _safe_auth_meta('', request_meta)
    try:
        token = RefreshToken(refresh_token)
        user_id = str(token.get('user_id') or '')
        if hasattr(token, 'blacklist'):
            token.blacklist()
    except Exception as exc:
        _audit_auth_event(
            event_type='auth.logout_failed',
            entity_id='unknown',
            context={**log_meta, 'status': 'failed', 'reason': 'invalid_refresh_token'},
        )
        raise AuthenticationFailed('Invalid refresh token') from exc
    _audit_auth_event(
        event_type='auth.logout',
        entity_id=user_id or 'unknown',
        context={**log_meta, 'status': 'success', 'user_id': user_id},
    )
    return {'status': 'logged_out'}


def current_session_payload(*, user) -> dict[str, Any]:
    if not user or not user.is_authenticated:
        return {'is_authenticated': False, 'user': None}
    return {'is_authenticated': True, 'user': get_account_payload(user)}
