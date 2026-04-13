from __future__ import annotations

from apps.tenancy import selectors


class TenancyService:
    def get_context(self) -> dict:
        context = selectors.get_tenant_context()
        return {
            'active_tenant': context.active_tenant,
            'memberships': context.memberships,
            'accessible_tenant_ids': context.accessible_tenant_ids,
        }

    def switch_active_tenant(self, tenant_code: str) -> dict:
        context = selectors.get_tenant_context()
        matched = next((m for m in context.memberships if m['tenant_code'] == tenant_code), None)
        if not matched:
            raise ValueError('tenant_not_accessible')
        return {
            'active_tenant': {
                'id': matched['tenant_id'],
                'code': matched['tenant_code'],
                'name': matched['tenant_name'],
                'kind': matched['tenant_kind'],
                'membership_role': matched['membership_role'],
                'permissions': matched['permissions'],
            },
            'status': 'switched',
        }
