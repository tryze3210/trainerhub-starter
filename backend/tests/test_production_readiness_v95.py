import pytest
from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework.test import APIClient

from apps.ops.production_readiness import get_platform_production_readiness


@pytest.mark.django_db
def test_v110_production_readiness_reports_platform_gate_categories():
    payload = get_platform_production_readiness()

    assert payload['version'] == 'v120'
    assert payload['scope'] == 'full platform production readiness'
    categories = {check['category'] for check in payload['checks']}
    assert {'api_contract', 'python_contract', 'permissions', 'files', 'executable_files', 'management_commands', 'auth_safety'}.issubset(categories)
    executable_check = next(check for check in payload['checks'] if check['key'] == 'backend_contracts_executable')
    assert executable_check['status'] == 'ok'
    auth_check = next(check for check in payload['checks'] if check['key'] == 'auth_login_throttle')
    assert auth_check['status'] == 'ok'
    register_check = next(check for check in payload['checks'] if check['key'] == 'auth_register_throttle')
    assert register_check['status'] == 'ok'
    refresh_check = next(check for check in payload['checks'] if check['key'] == 'auth_refresh_throttle')
    assert refresh_check['status'] == 'ok'
    cache_check = next(check for check in payload['checks'] if check['key'] == 'production_cache_backend')
    assert cache_check['status'] == 'ok'
    assert any(item['key'] == 'trainer_crm' for item in payload['frontend_surface'])
    assert any(item['key'] == 'trainer_schedule' for item in payload['frontend_surface'])
    assert any(item['key'] == 'messages' for item in payload['frontend_surface'])
    assert any(item['key'] == 'readiness_gate' for item in payload['smoke_commands'])
    assert any(item['key'] == 'launch_gate' for item in payload['smoke_commands'])
    assert any(item['role'] == 'trainer' for item in payload['role_matrix'])
    assert any(item['role'] == 'support' for item in payload['role_matrix'])
    assert any(item['role'] == 'finance' for item in payload['role_matrix'])
    assert any(item['role'] == 'readonly_auditor' for item in payload['role_matrix'])
    assert payload['ci_gate']['launch_script'] == 'scripts/ci/launch_gate.sh'


@pytest.mark.django_db
def test_admin_can_read_v110_production_readiness_endpoint():
    admin = get_user_model().objects.create_superuser(email='v95-admin@example.com', password='pass12345')
    client = APIClient()
    client.force_authenticate(user=admin)

    response = client.get('/api/v1/ops/admin/production-readiness/')

    assert response.status_code == 200
    payload = response.json()
    assert payload['version'] == 'v120'
    assert 'summary' in payload


@pytest.mark.django_db
@override_settings(
    IS_PRODUCTION=True,
    PAYMENTS_ALLOW_MOCK_PROVIDER=True,
    PAYMENTS_ALLOW_UNVERIFIED_PROVIDER_RETURN=True,
)
def test_v110_production_readiness_flags_unsafe_payment_production_settings():
    payload = get_platform_production_readiness()
    payment_check = next(check for check in payload['checks'] if check['key'] == 'payment_production_guards')

    assert payment_check['status'] == 'critical'
    assert set(payment_check['unsafe_flags']) == {
        'PAYMENTS_ALLOW_MOCK_PROVIDER',
        'PAYMENTS_ALLOW_UNVERIFIED_PROVIDER_RETURN',
    }
    assert payload['summary']['critical_count'] >= 1


@pytest.mark.django_db
@override_settings(
    IS_PRODUCTION=True,
    EMAIL_BACKEND='django.core.mail.backends.smtp.EmailBackend',
    DEFAULT_FROM_EMAIL='TrainerHub <no-reply@localhost>',
    EMAIL_HOST='localhost',
)
def test_v110_production_readiness_flags_unsafe_email_production_settings():
    payload = get_platform_production_readiness()
    email_check = next(check for check in payload['checks'] if check['key'] == 'email_production_config')

    assert email_check['status'] == 'critical'
    assert set(email_check['unsafe_flags']) == {'DEFAULT_FROM_EMAIL', 'EMAIL_HOST'}


@pytest.mark.django_db
@override_settings(
    IS_PRODUCTION=True,
    PAYOUTS_REQUIRE_LEGAL_ELIGIBILITY=False,
)
def test_v120_production_readiness_flags_disabled_payout_legal_gate():
    payload = get_platform_production_readiness()
    payout_check = next(check for check in payload['checks'] if check['key'] == 'payout_legal_eligibility_gate')

    assert payout_check['status'] == 'critical'
    assert payout_check['unsafe_flags'] == ['PAYOUTS_REQUIRE_LEGAL_ELIGIBILITY']


@pytest.mark.django_db
@override_settings(
    IS_PRODUCTION=True,
    REST_FRAMEWORK={
        "DEFAULT_THROTTLE_RATES": {
            "auth_login": "100/minute",
        },
    },
)
def test_v120_production_readiness_flags_unsafe_auth_login_throttle():
    payload = get_platform_production_readiness()
    auth_check = next(check for check in payload['checks'] if check['key'] == 'auth_login_throttle')

    assert auth_check['status'] == 'critical'
    assert auth_check['configured_rate'] == '100/minute'


@pytest.mark.django_db
@override_settings(
    IS_PRODUCTION=True,
    REST_FRAMEWORK={
        "DEFAULT_THROTTLE_RATES": {
            "auth_login": "10/minute",
            "auth_register": "120/hour",
        },
    },
)
def test_v120_production_readiness_flags_unsafe_auth_register_throttle():
    payload = get_platform_production_readiness()
    register_check = next(check for check in payload['checks'] if check['key'] == 'auth_register_throttle')

    assert register_check['status'] == 'critical'
    assert register_check['configured_rate'] == '120/hour'


@pytest.mark.django_db
@override_settings(
    IS_PRODUCTION=True,
    REST_FRAMEWORK={
        "DEFAULT_THROTTLE_RATES": {
            "auth_login": "10/minute",
            "auth_register": "20/hour",
            "auth_refresh": "300/minute",
        },
    },
)
def test_v120_production_readiness_flags_unsafe_auth_refresh_throttle():
    payload = get_platform_production_readiness()
    refresh_check = next(check for check in payload['checks'] if check['key'] == 'auth_refresh_throttle')

    assert refresh_check['status'] == 'critical'
    assert refresh_check['configured_rate'] == '300/minute'


@pytest.mark.django_db
@override_settings(
    IS_PRODUCTION=True,
    CACHES={
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "test",
        },
    },
)
def test_v120_production_readiness_flags_local_memory_cache_in_production():
    payload = get_platform_production_readiness()
    cache_check = next(check for check in payload['checks'] if check['key'] == 'production_cache_backend')

    assert cache_check['status'] == 'critical'
    assert 'LocMemCache' in cache_check['backend']
