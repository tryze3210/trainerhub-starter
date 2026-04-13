from __future__ import annotations

from apps.tenancy.models import TenantContext


def get_demo_memberships() -> list[dict]:
    return [
        {
            'tenant_id': 'tenant_trainer_001',
            'tenant_code': 'fit-anna',
            'tenant_name': 'Anna Fit Studio',
            'tenant_kind': 'trainer_space',
            'membership_role': 'owner',
            'status': 'active',
            'permissions': [
                'tenant.manage',
                'trainer_cms.manage_content',
                'media.upload',
                'moderation.view_own',
                'payouts.view_own',
            ],
        },
        {
            'tenant_id': 'tenant_platform_admin',
            'tenant_code': 'platform-core',
            'tenant_name': 'TrainerHub Platform',
            'tenant_kind': 'platform',
            'membership_role': 'admin',
            'status': 'active',
            'permissions': [
                'tenant.manage',
                'admin.moderation.review',
                'admin.payments.view',
                'admin.payouts.review',
            ],
        },
    ]


def get_active_tenant_code() -> str:
    return 'fit-anna'


def get_tenant_context() -> TenantContext:
    memberships = get_demo_memberships()
    active_code = get_active_tenant_code()
    active = next((m for m in memberships if m['tenant_code'] == active_code), memberships[0])
    return TenantContext(
        active_tenant={
            'id': active['tenant_id'],
            'code': active['tenant_code'],
            'name': active['tenant_name'],
            'kind': active['tenant_kind'],
            'membership_role': active['membership_role'],
            'permissions': active['permissions'],
        },
        memberships=memberships,
        accessible_tenant_ids=[m['tenant_id'] for m in memberships if m['status'] == 'active'],
    )
