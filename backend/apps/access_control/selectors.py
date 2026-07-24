from __future__ import annotations

from apps.accounts.models import AccountRoleAssignment
from apps.onboarding.selectors import build_status
from apps.tenancy import selectors as tenancy_selectors


ROLE_CAPABILITIES = {
    'user': ['cabinet.view_self', 'accounts.manage_self', 'learning.view', 'assignments.submit', 'messaging.use'],
    'trainer': [
        'cabinet.view_self',
        'accounts.manage_self',
        'trainer_cms.manage',
        'trainer_cms.manage_content',
        'media.upload',
        'media_assets.upload',
        'assignments.review',
        'messaging.use',
        'reviews.reply',
    ],
    'admin': ['cabinet.view_self', 'accounts.manage_self', 'moderation.review', 'payments.manage', 'payouts.manage', 'audit.view', 'ops.manage', 'notifications.manage'],
    'support': ['cabinet.view_self', 'accounts.manage_self', 'payments.view', 'orders.view', 'entitlements.view', 'audit.view', 'notifications.resend', 'messaging.support'],
    'finance': ['cabinet.view_self', 'accounts.manage_self', 'payments.view', 'payouts.view', 'payouts.manage', 'finance.view', 'finance.export'],
    'readonly_auditor': ['cabinet.view_self', 'accounts.manage_self', 'audit.view', 'ops.view', 'payments.view', 'payouts.view', 'readonly.audit'],
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
        'support_console': {'required_roles': ['admin', 'support'], 'required_steps': []},
        'finance_ops': {'required_roles': ['admin', 'finance'], 'required_steps': []},
        'readonly_audit': {'required_roles': ['admin', 'readonly_auditor'], 'required_steps': []},
        'tenant_settings': {'required_roles': ['trainer', 'admin'], 'required_steps': ['account_basics']},
    }


def get_object_registry() -> dict[str, dict[str, dict]]:
    return {
        'trainer_content': {},
        'media_asset': {},
        'moderation_case': {},
    }
