import pytest
from django.contrib.auth import get_user_model
from rest_framework.permissions import AllowAny
from rest_framework.test import APIRequestFactory

from apps.access_control.permissions import (
    ROLE_ADMIN,
    ROLE_FINANCE,
    ROLE_READONLY_AUDITOR,
    ROLE_STUDENT,
    ROLE_SUPPORT,
    IsAdminOrSupport,
    IsAdminSupportFinanceReadonly,
    IsAuditReader,
    CanManageTrainerCms,
    CanUploadMedia,
    IsFinanceOps,
    IsNotificationOperator,
    user_role_set,
)
from apps.accounts.models import AccountRoleAssignment
from apps.access_control.policies import PolicyService
from apps.audit.api.views import AuditAdminViewSet
from apps.messaging.api.views import CreateSystemMessageView
from apps.notifications.api.views import AdminNotificationCenterView
from apps.payments.api.views import AdminPaymentViewSet, PaymentWebhookViewSet
from apps.payouts.api.views import AdminPayoutViewSet
from apps.trainers.models import TrainerProfile


@pytest.fixture
def factory():
    return APIRequestFactory()


def _request(factory, method, user):
    request = getattr(factory, method.lower())('/api/v1/admin/test/')
    request.user = user
    return request


def _user(email, role=None):
    kwargs = {'email': email, 'password': 'pass12345'}
    if role:
        kwargs['role'] = role
    return get_user_model().objects.create_user(**kwargs)


def _assign(user, role):
    return AccountRoleAssignment.objects.create(user=user, role=role, is_active=True)


@pytest.mark.django_db
def test_v107_role_set_collects_primary_and_active_assignments():
    student = _user('v107-student@example.com')
    support = _user('v107-support@example.com')
    _assign(support, ROLE_SUPPORT)

    assert ROLE_STUDENT in user_role_set(student)
    assert ROLE_SUPPORT in user_role_set(support)


@pytest.mark.django_db
def test_v107_role_assignments_override_legacy_user_role():
    legacy_admin = _user('v107-legacy-admin@example.com', role=ROLE_ADMIN)
    _assign(legacy_admin, ROLE_SUPPORT)

    roles = user_role_set(legacy_admin)

    assert ROLE_SUPPORT in roles
    assert ROLE_ADMIN not in roles


def test_v107_role_assignment_errors_are_not_silently_hidden():
    class BrokenAssignments:
        def filter(self, **kwargs):
            raise RuntimeError('role store unavailable')

    class BrokenUser:
        is_authenticated = True
        is_staff = False
        is_superuser = False
        role = ROLE_ADMIN
        role_assignments = BrokenAssignments()

    with pytest.raises(RuntimeError, match='role store unavailable'):
        user_role_set(BrokenUser())


def test_v107_policy_feature_check_does_not_hide_runtime_context_errors(monkeypatch):
    def broken_context(*, user=None):
        raise RuntimeError('policy context unavailable')

    monkeypatch.setattr('apps.access_control.selectors.get_current_account_context', broken_context)

    with pytest.raises(RuntimeError, match='policy context unavailable'):
        PolicyService().check_feature(user=object(), feature_key='cabinet')


@pytest.mark.django_db
def test_v107_admin_support_finance_readonly_is_method_aware(factory):
    support = _user('v107-support-read@example.com')
    admin = _user('v107-admin-write@example.com')
    _assign(support, ROLE_SUPPORT)
    _assign(admin, ROLE_ADMIN)

    permission = IsAdminSupportFinanceReadonly()

    assert permission.has_permission(_request(factory, 'get', support), object()) is True
    assert permission.has_permission(_request(factory, 'post', support), object()) is False
    assert permission.has_permission(_request(factory, 'post', admin), object()) is True


@pytest.mark.django_db
def test_v107_finance_ops_allows_finance_writes_and_auditor_reads(factory):
    finance = _user('v107-finance@example.com')
    auditor = _user('v107-auditor@example.com')
    _assign(finance, ROLE_FINANCE)
    _assign(auditor, ROLE_READONLY_AUDITOR)

    permission = IsFinanceOps()

    assert permission.has_permission(_request(factory, 'post', finance), object()) is True
    assert permission.has_permission(_request(factory, 'get', auditor), object()) is True
    assert permission.has_permission(_request(factory, 'post', auditor), object()) is False


@pytest.mark.django_db
def test_v107_audit_and_notifications_keep_writes_admin_only(factory):
    support = _user('v107-support-audit@example.com')
    admin = _user('v107-admin-audit@example.com')
    _assign(support, ROLE_SUPPORT)
    _assign(admin, ROLE_ADMIN)

    audit_permission = IsAuditReader()
    notification_permission = IsNotificationOperator()

    assert audit_permission.has_permission(_request(factory, 'get', support), object()) is True
    assert audit_permission.has_permission(_request(factory, 'post', support), object()) is False
    assert notification_permission.has_permission(_request(factory, 'get', support), object()) is True
    assert notification_permission.has_permission(_request(factory, 'post', support), object()) is False
    assert notification_permission.has_permission(_request(factory, 'post', admin), object()) is True


@pytest.mark.django_db
def test_v107_trainer_policy_capabilities_match_permission_requirements(factory):
    trainer = _user('v107-trainer-policy@example.com')
    _assign(trainer, 'trainer')
    TrainerProfile.objects.create(
        user=trainer,
        slug='v107-trainer-policy',
        display_name='V107 Trainer Policy',
        status='active',
        is_public=True,
    )

    cms_request = _request(factory, 'post', trainer)
    upload_request = _request(factory, 'post', trainer)

    assert CanManageTrainerCms().has_permission(cms_request, object()) is True
    assert CanUploadMedia().has_permission(upload_request, object()) is True


def test_v107_admin_api_views_use_role_matrix_permissions():
    assert AdminPaymentViewSet.permission_classes == [IsAdminSupportFinanceReadonly]
    assert AdminPayoutViewSet.permission_classes == [IsFinanceOps]
    assert AuditAdminViewSet.permission_classes == [IsAuditReader]
    assert IsNotificationOperator in AdminNotificationCenterView.permission_classes
    assert CreateSystemMessageView.permission_classes == [IsAdminOrSupport]


def test_v107_payment_webhook_permissions_are_action_scoped():
    view = PaymentWebhookViewSet()

    view.action = 'receive'
    assert isinstance(view.get_permissions()[0], AllowAny)

    view.action = 'reprocess'
    assert isinstance(view.get_permissions()[0], IsAdminOrSupport)

    view.action = 'list'
    assert isinstance(view.get_permissions()[0], IsAdminSupportFinanceReadonly)
