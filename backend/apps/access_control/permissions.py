from __future__ import annotations

from rest_framework.permissions import BasePermission

from apps.access_control.policies import PolicyService


class PolicyPermission(BasePermission):
    required_capability: str | None = None
    required_feature: str | None = None
    message = 'Access denied by policy layer'
    policy_service = PolicyService()

    def has_permission(self, request, view) -> bool:
        decision = self.policy_service.require_feature(
            self.required_feature or 'cabinet',
            capability=self.required_capability,
        )
        if not decision.allowed:
            required = decision.required_capability or decision.feature_key or 'policy'
            self.message = f'{decision.reason}: {required}'
        return decision.allowed


class TenantObjectPermission(BasePermission):
    object_type_kwarg = 'object_type'
    object_id_kwarg = 'object_id'
    action = 'view'
    policy_service = PolicyService()
    message = 'Object access denied by tenant policy layer'

    def has_permission(self, request, view) -> bool:
        object_type = getattr(view, 'object_type', None) or view.kwargs.get(self.object_type_kwarg) or request.data.get('object_type')
        object_id = getattr(view, 'object_id', None) or view.kwargs.get(self.object_id_kwarg) or request.data.get('object_id')
        decision = self.policy_service.require_object_access(object_type, object_id, self.action)
        if not decision.allowed:
            self.message = decision.reason
        return decision.allowed


class CanAccessCabinet(PolicyPermission):
    required_feature = 'cabinet'
    required_capability = 'cabinet.view_self'


class CanManageTrainerCms(PolicyPermission):
    required_feature = 'trainer_cms'
    required_capability = 'trainer_cms.manage_content'


class CanUploadMedia(PolicyPermission):
    required_feature = 'media_upload'
    required_capability = 'media.upload'


class CanReviewModeration(PolicyPermission):
    required_feature = 'admin_moderation'
    required_capability = 'admin.moderation.review'


class CanEditTrainerContent(TenantObjectPermission):
    action = 'edit'


class CanDeleteMediaAsset(TenantObjectPermission):
    action = 'delete'
