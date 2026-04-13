from __future__ import annotations

from apps.accounts.models import AccountRoleAssignment
from apps.onboarding.selectors import build_status
from apps.tenancy import selectors as tenancy_selectors


ROLE_CAPABILITIES = {
    'user': ['cabinet.view_self', 'accounts.manage_self'],
    'trainer': ['cabinet.view_self', 'accounts.manage_self', 'trainer_cms.manage', 'media_assets.upload'],
    'admin': ['cabinet.view_self', 'accounts.manage_self', 'moderation.review', 'payments.manage', 'audit.view'],
}


def get_role_capabilities(role: str) -> list[str]:
    return ROLE_CAPABILITIES.get(role, [])


def get_current_account_context(*, user=None) -> dict:
    tenant_context = tenancy_selectors.get_tenant_context()
    active_tenant = tenant_context.active_tenant
    if user and getattr(user, 'is_authenticated', False):
        roles = list(user.role_assignments.order_by('role').values_list('role', flat=True)) or [AccountRoleAssignment.ROLE_USER]
        active_role = user.role_assignments.filter(is_active=True).values_list('role', flat=True).first() or AccountRoleAssignment.ROLE_USER
        onboarding_status = build_status(user=user)
        completed_steps = [step['code'] for step in onboarding_status['steps'] if step['is_completed']]
        account = {'id': str(user.pk), 'email': user.email}
    else:
        roles = ['user']
        active_role = 'user'
        completed_steps = []
        account = {'id': None, 'email': None}
    capabilities = sorted(set((active_tenant.get('permissions') or []) + get_role_capabilities(active_role)))
    return {
        'account': account,
        'active_role': active_role,
        'available_roles': roles,
        'capabilities': capabilities,
        'completed_steps': completed_steps,
        'active_tenant': active_tenant,
        'memberships': tenant_context.memberships,
    }


def get_feature_matrix() -> dict:
    return {
        'cabinet': {'required_roles': ['user', 'trainer', 'admin'], 'required_steps': ['account_basics']},
        'trainer_cms': {'required_roles': ['trainer'], 'required_steps': ['trainer_profile']},
        'media_upload': {'required_roles': ['trainer'], 'required_steps': ['trainer_profile']},
        'admin_moderation': {'required_roles': ['admin'], 'required_steps': []},
        'tenant_settings': {'required_roles': ['trainer', 'admin'], 'required_steps': ['account_basics']},
    }


def get_object_registry() -> dict[str, dict[str, dict]]:
    return {
        'trainer_content': {},
        'media_asset': {},
        'moderation_case': {},
    }
