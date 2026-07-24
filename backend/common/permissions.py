from rest_framework.permissions import BasePermission

from apps.access_control.permissions import ROLE_ADMIN, ROLE_TRAINER, user_role_set


class IsTrainer(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and ROLE_TRAINER in user_role_set(request.user))


class IsAdminRole(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and ROLE_ADMIN in user_role_set(request.user))
