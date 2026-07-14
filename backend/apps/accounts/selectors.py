from __future__ import annotations

from django.contrib.auth import get_user_model

from apps.accounts.models import AccountProfile, AccountRoleAssignment, AccountSettings

User = get_user_model()


def _fallback_name(user) -> str:
    full_name = (user.get_full_name() or '').strip()
    if full_name:
        return full_name
    email = (getattr(user, 'email', '') or '').strip()
    if email and '@' in email:
        return email.split('@', 1)[0]
    return 'User'


def _get_or_create_profile(user):
    fallback_name = _fallback_name(user)
    profile, _ = AccountProfile.objects.get_or_create(
        user=user,
        defaults={
            'full_name': fallback_name,
            'display_name': getattr(user, 'first_name', '') or fallback_name,
        },
    )
    return profile


def _get_or_create_settings(user):
    settings_obj, _ = AccountSettings.objects.get_or_create(user=user)
    return settings_obj


def _ensure_default_role(user):
    if not user.role_assignments.exists():
        AccountRoleAssignment.objects.create(user=user, role=AccountRoleAssignment.ROLE_USER, is_active=True)


def _is_staff_admin(user) -> bool:
    return bool(getattr(user, 'is_staff', False) or getattr(user, 'is_superuser', False))


def get_account_payload(user) -> dict:
    _ensure_default_role(user)
    profile = _get_or_create_profile(user)
    settings_obj = _get_or_create_settings(user)
    roles = list(user.role_assignments.order_by('role').values_list('role', flat=True))
    active_role = user.role_assignments.filter(is_active=True).values_list('role', flat=True).first() or AccountRoleAssignment.ROLE_USER
    is_staff_admin = _is_staff_admin(user)

    if is_staff_admin and AccountRoleAssignment.ROLE_ADMIN not in roles:
        roles.append(AccountRoleAssignment.ROLE_ADMIN)
        roles.sort()
    if is_staff_admin:
        active_role = AccountRoleAssignment.ROLE_ADMIN

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
        'is_staff': bool(getattr(user, 'is_staff', False)),
        'is_superuser': bool(getattr(user, 'is_superuser', False)),
        'settings': {
            'marketing_emails_enabled': settings_obj.marketing_emails_enabled,
            'product_updates_enabled': settings_obj.product_updates_enabled,
            'push_notifications_enabled': settings_obj.push_notifications_enabled,
            'favorite_categories': settings_obj.favorite_categories,
        },
    }
