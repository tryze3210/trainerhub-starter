def build_tenant_context() -> dict:
    return {
        'active_tenant': {
            'tenant_id': 'tenant_demo',
            'tenant_name': 'Demo Tenant',
            'membership_role': 'owner',
        },
        'memberships': [
            {
                'tenant_id': 'tenant_demo',
                'tenant_name': 'Demo Tenant',
                'membership_role': 'owner',
            }
        ],
    }
