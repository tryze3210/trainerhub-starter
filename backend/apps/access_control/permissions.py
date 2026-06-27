from __future__ import annotations

from rest_framework.permissions import BasePermission
from rest_framework.permissions import SAFE_METHODS

from apps.access_control.policies import PolicyService


ROLE_USER = 'user'
ROLE_STUDENT = 'student'
ROLE_TRAINER = 'trainer'
ROLE_ADMIN = 'admin'
ROLE_SUPPORT = 'support'
ROLE_FINANCE = 'finance'
ROLE_READONLY_AUDITOR = 'readonly_auditor'


def user_role_set(user) -> set[str]:
    if not user or not getattr(user, 'is_authenticated', False):
        return set()
    roles = set()
    primary = getattr(user, 'role', None)
    if primary:
        roles.add(str(primary))
        if primary in {'customer', ROLE_USER}:
            roles.add(ROLE_USER)
            roles.add(ROLE_STUDENT)
    try:
        assignments = user.role_assignments.filter(is_active=True).values_list('role', flat=True)
        roles.update(str(role) for role in assignments)
    except Exception:
        pass
    if getattr(user, 'is_staff', False) or getattr(user, 'is_superuser', False):
        roles.add(ROLE_ADMIN)
    return roles


class HasAnyRole(BasePermission):
    allowed_roles: set[str] = set()
    message = 'Required role is missing.'

    def has_permission(self, request, view) -> bool:
        roles = user_role_set(request.user)
        return bool(roles.intersection(self.allowed_roles))


class RoleMatrixPermission(BasePermission):
    read_roles: set[str] = set()
    write_roles: set[str] = set()
    message = 'Access denied by role matrix.'

    def has_permission(self, request, view) -> bool:
        roles = user_role_set(request.user)
        required = self.read_roles if request.method in SAFE_METHODS else self.write_roles
        return bool(roles.intersection(required))


class IsAdminRole(HasAnyRole):
    allowed_roles = {ROLE_ADMIN}


class IsTrainerRole(HasAnyRole):
    allowed_roles = {ROLE_TRAINER, ROLE_ADMIN}


class IsStudentRole(HasAnyRole):
    allowed_roles = {ROLE_USER, ROLE_STUDENT, ROLE_TRAINER, ROLE_ADMIN}


class IsSupportRole(HasAnyRole):
    allowed_roles = {ROLE_SUPPORT, ROLE_ADMIN}


class IsFinanceRole(HasAnyRole):
    allowed_roles = {ROLE_FINANCE, ROLE_ADMIN}


class IsReadonlyAuditorRole(HasAnyRole):
    allowed_roles = {ROLE_READONLY_AUDITOR, ROLE_ADMIN}


class IsAdminOrSupport(HasAnyRole):
    allowed_roles = {ROLE_ADMIN, ROLE_SUPPORT}


class IsAdminOrFinance(HasAnyRole):
    allowed_roles = {ROLE_ADMIN, ROLE_FINANCE}


class IsAdminSupportFinanceReadonly(RoleMatrixPermission):
    read_roles = {ROLE_ADMIN, ROLE_SUPPORT, ROLE_FINANCE, ROLE_READONLY_AUDITOR}
    write_roles = {ROLE_ADMIN}


class IsFinanceOps(RoleMatrixPermission):
    read_roles = {ROLE_ADMIN, ROLE_FINANCE, ROLE_READONLY_AUDITOR}
    write_roles = {ROLE_ADMIN, ROLE_FINANCE}


class IsAuditReader(RoleMatrixPermission):
    read_roles = {ROLE_ADMIN, ROLE_SUPPORT, ROLE_READONLY_AUDITOR}
    write_roles = {ROLE_ADMIN}


class IsNotificationOperator(RoleMatrixPermission):
    read_roles = {ROLE_ADMIN, ROLE_SUPPORT, ROLE_READONLY_AUDITOR}
    write_roles = {ROLE_ADMIN}


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
