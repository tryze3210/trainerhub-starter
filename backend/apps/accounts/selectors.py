from __future__ import annotations

from django.contrib.auth import get_user_model

from apps.accounts.models import AccountProfile, AccountRoleAssignment, AccountSettings

User = get_user_model()


def _get_or_create_profile(user):
    profile, _ = AccountProfile.objects.get_or_create(
        user=user,
        defaults={
            'full_name': user.get_full_name() or user.username,
            'display_name': user.first_name or '',
        },
    )
    return profile


def _get_or_create_settings(user):
    settings_obj, _ = AccountSettings.objects.get_or_create(user=user)
    return settings_obj


def _ensure_default_role(user):
    if not user.role_assignments.exists():
        AccountRoleAssignment.objects.create(user=user, role=AccountRoleAssignment.ROLE_USER, is_active=True)


def get_account_payload(user) -> dict:
    _ensure_default_role(user)
    profile = _get_or_create_profile(user)
    settings_obj = _get_or_create_settings(user)
    roles = list(user.role_assignments.order_by('role').values_list('role', flat=True))
    active_role = user.role_assignments.filter(is_active=True).values_list('role', flat=True).first() or AccountRoleAssignment.ROLE_USER
    return {
        'id': str(user.pk),
        'email': user.email,
        'full_name': profile.full_name,
        'display_name': profile.display_name,
        'phone': profile.phone,
        'country': profile.country,
        'city': profile.city,
        'timezone': profile.timezone,
        'preferred_language': profile.preferred_language,
        'active_role': active_role,
        'available_roles': roles,
        'settings': {
            'marketing_emails_enabled': settings_obj.marketing_emails_enabled,
            'product_updates_enabled': settings_obj.product_updates_enabled,
            'push_notifications_enabled': settings_obj.push_notifications_enabled,
            'favorite_categories': settings_obj.favorite_categories,
        },
    }
