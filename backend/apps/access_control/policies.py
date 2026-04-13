from __future__ import annotations

from typing import Any

from apps.access_control import selectors
from apps.access_control.models import FeatureGateResult, ObjectPolicyDecision, PolicyDecision


class PolicyService:
    def get_access_snapshot(self, *, user=None) -> dict[str, Any]:
        context = selectors.get_current_account_context(user=user)
        feature_gates = {
            key: self.feature_gate(key, context=context)
            for key in selectors.get_feature_matrix().keys()
        }
        return {
            'account': {
                'id': context['account'].get('id'),
                'email': context['account'].get('email'),
                'active_role': context['active_role'],
                'available_roles': context['available_roles'],
            },
            'tenant': context['active_tenant'],
            'capabilities': context['capabilities'],
            'completed_steps': context['completed_steps'],
            'feature_gates': {
                key: {
                    'key': value.key,
                    'enabled': value.enabled,
                    'reason': value.reason,
                    'required_role': value.required_role,
                    'required_onboarding_steps': value.required_onboarding_steps,
                }
                for key, value in feature_gates.items()
            },
        }

    def feature_gate(self, feature_key: str, *, context: dict[str, Any] | None = None, user=None) -> FeatureGateResult:
        context = context or selectors.get_current_account_context(user=user)
        matrix = selectors.get_feature_matrix().get(feature_key)
        if not matrix:
            return FeatureGateResult(key=feature_key, enabled=False, reason='feature_not_registered')
        active_role = context['active_role']
        completed_steps = set(context['completed_steps'])
        required_roles = matrix.get('required_roles', [])
        required_steps = matrix.get('required_steps', [])
        if required_roles and active_role not in required_roles:
            return FeatureGateResult(key=feature_key, enabled=False, reason='role_not_allowed', required_role=required_roles[0], required_onboarding_steps=required_steps)
        missing_steps = [step for step in required_steps if step not in completed_steps]
        if missing_steps:
            return FeatureGateResult(key=feature_key, enabled=False, reason='onboarding_incomplete', required_role=active_role, required_onboarding_steps=missing_steps)
        return FeatureGateResult(key=feature_key, enabled=True, reason='enabled', required_role=active_role, required_onboarding_steps=[])

    def require_capability(self, capability: str, *, context: dict[str, Any] | None = None, user=None) -> PolicyDecision:
        context = context or selectors.get_current_account_context(user=user)
        allowed = capability in context['capabilities']
        return PolicyDecision(allowed=allowed, code='allowed' if allowed else 'missing_capability', reason='allowed' if allowed else f'Capability {capability} is required', required_capability=None if allowed else capability, context={'active_role': context['active_role'], 'tenant_id': context['active_tenant']['id']})

    def require_feature(self, feature_key: str, *, capability: str | None = None, context: dict[str, Any] | None = None, user=None) -> PolicyDecision:
        context = context or selectors.get_current_account_context(user=user)
        if capability:
            capability_decision = self.require_capability(capability, context=context)
            if not capability_decision.allowed:
                return capability_decision
        feature = self.feature_gate(feature_key, context=context)
        return PolicyDecision(allowed=feature.enabled, code='allowed' if feature.enabled else feature.reason, reason=feature.reason, required_capability=capability, feature_key=feature_key, context={'active_role': context['active_role'], 'tenant_id': context['active_tenant']['id'], 'required_onboarding_steps': feature.required_onboarding_steps})

    def require_object_access(self, object_type: str, object_id: str, action: str, *, context: dict[str, Any] | None = None, user=None) -> ObjectPolicyDecision:
        context = context or selectors.get_current_account_context(user=user)
        registry = selectors.get_object_registry().get(object_type, {})
        obj = registry.get(object_id)
        actor_account_id = context['account']['id']
        actor_role = context['active_role']
        active_tenant_id = context['active_tenant']['id']
        if not obj:
            return ObjectPolicyDecision(allowed=False, code='object_not_found', reason='Object is not registered in policy registry', object_type=object_type, object_id=object_id, action=action, actor_account_id=actor_account_id, actor_role=actor_role, tenant_id=active_tenant_id)
        return ObjectPolicyDecision(allowed=True, code='allowed', reason='allowed', object_type=object_type, object_id=object_id, action=action, tenant_id=obj['tenant_id'], owner_account_id=obj['owner_account_id'], actor_account_id=actor_account_id, actor_role=actor_role, context={'active_tenant_id': active_tenant_id})
