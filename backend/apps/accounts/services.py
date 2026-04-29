from __future__ import annotations

from typing import Any

from django.db import transaction

from apps.accounts.models import AccountProfile, AccountRoleAssignment, AccountSettings
from apps.accounts.selectors import get_account_payload
from apps.access_control.selectors import get_role_capabilities

ROLE_QUICK_LINKS = {
    'user': [
        {'label': 'Catalog', 'href': '/catalog'},
        {'label': 'Favorites', 'href': '/favorites'},
        {'label': 'Library', 'href': '/library'},
    ],
    'trainer': [
        {'label': 'Trainer CMS', 'href': '/trainer/cms'},
        {'label': 'Media', 'href': '/trainer/media'},
        {'label': 'Payouts', 'href': '/trainer/payouts'},
    ],
    'admin': [
        {'label': 'Moderation', 'href': '/admin/moderation'},
        {'label': 'Payments', 'href': '/admin/payments'},
        {'label': 'Audit', 'href': '/admin/audit'},
    ],
}


def _resolve_user(*, user=None, request=None):
    return user or getattr(request, 'user', None)


def _fallback_name(user) -> str:
    full_name = (user.get_full_name() or '').strip()
    if full_name:
        return full_name
    email = (getattr(user, 'email', '') or '').strip()
    if email and '@' in email:
        return email.split('@', 1)[0]
    return 'User'


def get_profile(*, user=None, request=None) -> dict[str, Any]:
    resolved = _resolve_user(user=user, request=request)
    if resolved is None:
        return {}
    if hasattr(resolved, 'account_profile') or hasattr(resolved, 'role_assignments'):
        return get_account_payload(resolved)
    profile = getattr(resolved, 'profile', None)
    return {
        'display_name': getattr(profile, 'display_name', ''),
        'email': getattr(resolved, 'email', ''),
    }


@transaction.atomic
def update_profile(*, user, payload: dict[str, Any]) -> dict[str, Any]:
    profile, _ = AccountProfile.objects.get_or_create(user=user, defaults={'full_name': _fallback_name(user)})
    for field in ['full_name', 'display_name', 'phone', 'country', 'city', 'timezone', 'preferred_language']:
        if field in payload:
            setattr(profile, field, payload[field])
    if not profile.full_name:
        profile.full_name = _fallback_name(user)
    if not profile.display_name:
        profile.display_name = profile.full_name
    profile.save()
    return get_account_payload(user)


def get_settings(*, user) -> dict[str, Any]:
    return get_account_payload(user)['settings']


@transaction.atomic
def update_settings(*, user, payload: dict[str, Any]) -> dict[str, Any]:
    settings_obj, _ = AccountSettings.objects.get_or_create(user=user)
    for field in ['marketing_emails_enabled', 'product_updates_enabled', 'push_notifications_enabled', 'favorite_categories']:
        if field in payload:
            setattr(settings_obj, field, payload[field])
    settings_obj.save()
    return get_account_payload(user)['settings']


@transaction.atomic
def switch_role(*, user, role: str) -> dict[str, Any]:
    assignment = user.role_assignments.filter(role=role).first()
    if assignment is None:
        raise ValueError(f'Role {role} is not assigned to current account')
    user.role_assignments.filter(is_active=True).update(is_active=False)
    assignment.is_active = True
    assignment.save()
    return {
        'active_role': role,
        'available_roles': list(user.role_assignments.order_by('role').values_list('role', flat=True)),
        'role_capabilities': get_role_capabilities(role),
    }


def get_cabinet(*, user) -> dict[str, Any]:
    account = get_account_payload(user)
    active_role = account['active_role']
    return {
        'account': account,
        'quick_links': ROLE_QUICK_LINKS.get(active_role, []),
        'role_capabilities': get_role_capabilities(active_role),
        'stats': {
            'favorites_count': len(account['settings']['favorite_categories']),
            'active_entitlements_count': 0,
            'draft_content_count': 0,
            'unread_notifications_count': 0,
        },
    }
