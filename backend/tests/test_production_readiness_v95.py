import pytest
from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.test import APIClient

from apps.ops.api import views as ops_views
from apps.ops.production_readiness import get_platform_production_readiness


@pytest.mark.django_db
def test_v110_production_readiness_reports_platform_gate_categories():
    payload = get_platform_production_readiness()

    assert payload['version'] == 'v120'
    assert payload['scope'] == 'full platform production readiness'
    categories = {check['category'] for check in payload['checks']}
    assert {
        'api_contract',
        'audit_safety',
        'python_contract',
        'permissions',
        'files',
        'executable_files',
        'management_commands',
        'auth_safety',
        'backup_safety',
        'database_safety',
        'http_safety',
        'observability_safety',
        'payout_safety',
        'privacy_safety',
        'settings_safety',
        'storage_safety',
        'task_safety',
        'deploy_safety',
        'export_safety',
    }.issubset(categories)
    executable_check = next(check for check in payload['checks'] if check['key'] == 'backend_contracts_executable')
    assert executable_check['status'] == 'ok'
    auth_check = next(check for check in payload['checks'] if check['key'] == 'auth_login_throttle')
    assert auth_check['status'] == 'ok'
    register_check = next(check for check in payload['checks'] if check['key'] == 'auth_register_throttle')
    assert register_check['status'] == 'ok'
    refresh_check = next(check for check in payload['checks'] if check['key'] == 'auth_refresh_throttle')
    assert refresh_check['status'] == 'ok'
    logout_check = next(check for check in payload['checks'] if check['key'] == 'auth_logout_throttle')
    assert logout_check['status'] == 'ok'
    public_ingest_check = next(check for check in payload['checks'] if check['key'] == 'public_ingest_throttles')
    assert public_ingest_check['status'] == 'ok'
    admin_ops_throttle_check = next(check for check in payload['checks'] if check['key'] == 'admin_ops_throttle')
    assert admin_ops_throttle_check['status'] == 'ok'
    cache_check = next(check for check in payload['checks'] if check['key'] == 'production_cache_backend')
    assert cache_check['status'] == 'ok'
    media_storage_check = next(check for check in payload['checks'] if check['key'] == 'media_storage_production_config')
    assert media_storage_check['status'] == 'ok'
    media_upload_check = next(check for check in payload['checks'] if check['key'] == 'media_upload_validation_contract')
    assert media_upload_check['status'] == 'ok'
    media_upload_permission_check = next(check for check in payload['checks'] if check['key'] == 'media_upload_permission_contract')
    assert media_upload_permission_check['status'] == 'ok'
    media_upload_verification_check = next(check for check in payload['checks'] if check['key'] == 'media_upload_verification_contract')
    assert media_upload_verification_check['status'] == 'ok'
    media_read_ttl_check = next(check for check in payload['checks'] if check['key'] == 'media_read_ttl_contract')
    assert media_read_ttl_check['status'] == 'ok'
    csv_export_check = next(check for check in payload['checks'] if check['key'] == 'csv_export_safety_contract')
    assert csv_export_check['status'] == 'ok'
    backup_restore_check = next(check for check in payload['checks'] if check['key'] == 'backup_restore_contract')
    assert backup_restore_check['status'] == 'ok'
    celery_check = next(check for check in payload['checks'] if check['key'] == 'celery_production_config')
    assert celery_check['status'] == 'ok'
    error_tracking_check = next(check for check in payload['checks'] if check['key'] == 'error_tracking_production_config')
    assert error_tracking_check['status'] == 'ok'
    namespace_check = next(check for check in payload['checks'] if check['key'] == 'runtime_apps_namespace')
    assert namespace_check['status'] == 'ok'
    settings_layout_check = next(check for check in payload['checks'] if check['key'] == 'django_settings_layout')
    assert settings_layout_check['status'] == 'ok'
    release_job_check = next(check for check in payload['checks'] if check['key'] == 'backend_migration_release_job')
    assert release_job_check['status'] == 'ok'
    celery_worker_queues_check = next(check for check in payload['checks'] if check['key'] == 'celery_worker_queue_coverage')
    assert celery_worker_queues_check['status'] == 'ok'
    outbox_overlay_check = next(check for check in payload['checks'] if check['key'] == 'outbox_compose_overlay_runtime')
    assert outbox_overlay_check['status'] == 'ok'
    deploy_preflight_check = next(check for check in payload['checks'] if check['key'] == 'deploy_scripts_preflight')
    assert deploy_preflight_check['status'] == 'ok'
    deploy_image_tag_check = next(check for check in payload['checks'] if check['key'] == 'deploy_image_tag_contract')
    assert deploy_image_tag_check['status'] == 'ok'
    docker_context_check = next(check for check in payload['checks'] if check['key'] == 'docker_build_context_hygiene')
    assert docker_context_check['status'] == 'ok'
    frontend_runtime_check = next(check for check in payload['checks'] if check['key'] == 'frontend_standalone_runtime')
    assert frontend_runtime_check['status'] == 'ok'
    nginx_check = next(check for check in payload['checks'] if check['key'] == 'nginx_edge_proxy_contract')
    assert nginx_check['status'] == 'ok'
    cookie_auth_check = next(check for check in payload['checks'] if check['key'] == 'cookie_jwt_authentication')
    assert cookie_auth_check['status'] == 'ok'
    provider_return_check = next(check for check in payload['checks'] if check['key'] == 'provider_return_read_only')
    assert provider_return_check['status'] == 'ok'
    webhook_signature_check = next(check for check in payload['checks'] if check['key'] == 'public_webhook_signature_path')
    assert webhook_signature_check['status'] == 'ok'
    webhook_body_limit_check = next(check for check in payload['checks'] if check['key'] == 'public_webhook_body_limit')
    assert webhook_body_limit_check['status'] == 'ok'
    payment_gateway_urls_check = next(check for check in payload['checks'] if check['key'] == 'payment_gateway_public_urls')
    assert payment_gateway_urls_check['status'] == 'ok'
    commission_policy_check = next(check for check in payload['checks'] if check['key'] == 'commission_policy_single_source')
    assert commission_policy_check['status'] == 'ok'
    payout_ownership_check = next(check for check in payload['checks'] if check['key'] == 'payment_payout_ownership_source')
    assert payout_ownership_check['status'] == 'ok'
    side_effect_check = next(check for check in payload['checks'] if check['key'] == 'side_effect_failure_audit')
    assert side_effect_check['status'] == 'ok'
    default_permissions_check = next(check for check in payload['checks'] if check['key'] == 'default_api_permissions')
    assert default_permissions_check['status'] == 'ok'
    audit_redaction_check = next(check for check in payload['checks'] if check['key'] == 'audit_context_redaction')
    assert audit_redaction_check['status'] == 'ok'
    public_review_check = next(check for check in payload['checks'] if check['key'] == 'public_review_disclosure_contract')
    assert public_review_check['status'] == 'ok'
    review_self_check = next(check for check in payload['checks'] if check['key'] == 'review_self_moderation_contract')
    assert review_self_check['status'] == 'ok'
    review_throttle_check = next(check for check in payload['checks'] if check['key'] == 'review_write_throttle_contract')
    assert review_throttle_check['status'] == 'ok'
    review_reply_state_check = next(check for check in payload['checks'] if check['key'] == 'review_reply_state_contract')
    assert review_reply_state_check['status'] == 'ok'
    public_store_check = next(check for check in payload['checks'] if check['key'] == 'public_store_identity_contract')
    assert public_store_check['status'] == 'ok'
    messaging_privacy_check = next(check for check in payload['checks'] if check['key'] == 'messaging_participant_privacy_contract')
    assert messaging_privacy_check['status'] == 'ok'
    messaging_throttle_check = next(check for check in payload['checks'] if check['key'] == 'messaging_write_throttle_contract')
    assert messaging_throttle_check['status'] == 'ok'
    rbac_check = next(check for check in payload['checks'] if check['key'] == 'rbac_role_assignment_source')
    assert rbac_check['status'] == 'ok'
    trainer_runtime_role_check = next(check for check in payload['checks'] if check['key'] == 'trainer_runtime_role_source')
    assert trainer_runtime_role_check['status'] == 'ok'
    assignment_ownership_check = next(check for check in payload['checks'] if check['key'] == 'assignment_content_ownership_contract')
    assert assignment_ownership_check['status'] == 'ok'
    assignment_throttle_check = next(check for check in payload['checks'] if check['key'] == 'assignment_write_throttle_contract')
    assert assignment_throttle_check['status'] == 'ok'
    assignment_attachment_check = next(check for check in payload['checks'] if check['key'] == 'assignment_attachment_validation_contract')
    assert assignment_attachment_check['status'] == 'ok'
    progress_canonical_check = next(check for check in payload['checks'] if check['key'] == 'progress_canonical_program_contract')
    assert progress_canonical_check['status'] == 'ok'
    progress_throttle_check = next(check for check in payload['checks'] if check['key'] == 'progress_write_throttle_contract')
    assert progress_throttle_check['status'] == 'ok'
    progress_privacy_check = next(check for check in payload['checks'] if check['key'] == 'progress_student_privacy_contract')
    assert progress_privacy_check['status'] == 'ok'
    tenant_scoping_check = next(check for check in payload['checks'] if check['key'] == 'tenant_scoping_ownership_source')
    assert tenant_scoping_check['status'] == 'ok'
    entitlement_source_selection_check = next(
        check for check in payload['checks'] if check['key'] == 'entitlement_valid_source_selection_contract'
    )
    assert entitlement_source_selection_check['status'] == 'ok'
    support_entitlement_fix_check = next(
        check for check in payload['checks'] if check['key'] == 'support_entitlement_fix_target_contract'
    )
    assert support_entitlement_fix_check['status'] == 'ok'
    support_delivery_scope_check = next(
        check for check in payload['checks'] if check['key'] == 'support_notification_delivery_scope_contract'
    )
    assert support_delivery_scope_check['status'] == 'ok'
    database_check = next(check for check in payload['checks'] if check['key'] == 'production_database_backend')
    assert database_check['status'] == 'ok'
    origin_check = next(check for check in payload['checks'] if check['key'] == 'production_origin_security')
    assert origin_check['status'] == 'ok'
    payout_integrity_check = next(check for check in payload['checks'] if check['key'] == 'payout_runtime_recipient_integrity')
    assert payout_integrity_check['status'] == 'ok'
    public_runtime_check = next(check for check in payload['checks'] if check['key'] == 'public_runtime_readiness_disclosure')
    assert public_runtime_check['status'] == 'ok'
    demo_seed_guard_check = next(check for check in payload['checks'] if check['key'] == 'demo_seed_production_guard')
    assert demo_seed_guard_check['status'] == 'ok'
    production_gate_origins_check = next(check for check in payload['checks'] if check['key'] == 'production_gate_https_origin_defaults')
    assert production_gate_origins_check['status'] == 'ok'
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


def test_v120_admin_ops_views_use_scoped_throttle(settings):
    assert settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]["admin_ops"] == "60/minute"
    for view_class in (
        ops_views.AdminOperationsDashboardView,
        ops_views.AdminOperationsHubView,
        ops_views.AdminProductionReadinessView,
        ops_views.AdminObservabilityRuntimeView,
        ops_views.AdminGlobalSearchView,
        ops_views.SupportConsoleView,
        ops_views.SupportNotificationResendView,
        ops_views.SupportEntitlementFixView,
        ops_views.AdminReconciliationReportView,
        ops_views.AdminReconciliationRepairView,
        ops_views.AdminReconciliationSnapshotCaptureView,
        ops_views.AdminReconciliationSnapshotCompareView,
    ):
        assert view_class.throttle_classes == [ScopedRateThrottle]
        assert view_class.throttle_scope == "admin_ops"


@pytest.mark.django_db
@override_settings(
    IS_PRODUCTION=True,
    PAYMENTS_ALLOW_MOCK_PROVIDER=True,
    PAYMENTS_ALLOW_UNVERIFIED_PROVIDER_RETURN=True,
    PAYMENTS_WEBHOOK_REQUIRE_TIMESTAMP=False,
)
def test_v110_production_readiness_flags_unsafe_payment_production_settings():
    payload = get_platform_production_readiness()
    payment_check = next(check for check in payload['checks'] if check['key'] == 'payment_production_guards')

    assert payment_check['status'] == 'critical'
    assert set(payment_check['unsafe_flags']) == {
        'PAYMENTS_ALLOW_MOCK_PROVIDER',
        'PAYMENTS_ALLOW_UNVERIFIED_PROVIDER_RETURN',
        'PAYMENTS_WEBHOOK_REQUIRE_TIMESTAMP',
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
    VK_S3_ENDPOINT_URL='http://localhost:9000',
    VK_S3_ACCESS_KEY_ID='change-me',
    VK_S3_SECRET_ACCESS_KEY='secret-key',
    VK_PRIVATE_BUCKET='trainerhub-media',
    VK_PUBLIC_BUCKET='trainerhub-media',
)
def test_v120_production_readiness_flags_unsafe_media_storage_settings():
    payload = get_platform_production_readiness()
    storage_check = next(check for check in payload['checks'] if check['key'] == 'media_storage_production_config')

    assert storage_check['status'] == 'critical'
    assert set(storage_check['unsafe_flags']) == {
        'VK_S3_ENDPOINT_URL',
        'VK_S3_ACCESS_KEY_ID',
        'VK_BUCKETS_NOT_SEPARATED',
    }


@pytest.mark.django_db
@override_settings(
    IS_PRODUCTION=True,
    MEDIA_READ_TTL_SECONDS=3600,
    MEDIA_READ_MAX_TTL_SECONDS=3600,
)
def test_v120_production_readiness_flags_unsafe_media_read_ttl():
    payload = get_platform_production_readiness()
    ttl_check = next(check for check in payload['checks'] if check['key'] == 'media_read_ttl_contract')

    assert ttl_check['status'] == 'critical'
    assert 'MEDIA_READ_MAX_TTL_SECONDS_too_high' in ttl_check['offenders']


@pytest.mark.django_db
@override_settings(
    IS_PRODUCTION=True,
    CELERY_BROKER_URL='redis://localhost:6379/1',
    CELERY_RESULT_BACKEND='redis://redis:6379/2',
    CELERY_TASK_ALWAYS_EAGER=True,
)
def test_v120_production_readiness_flags_unsafe_celery_settings():
    payload = get_platform_production_readiness()
    celery_check = next(check for check in payload['checks'] if check['key'] == 'celery_production_config')

    assert celery_check['status'] == 'critical'
    assert set(celery_check['unsafe_flags']) == {'CELERY_BROKER_URL', 'CELERY_TASK_ALWAYS_EAGER'}


@pytest.mark.django_db
@override_settings(
    IS_PRODUCTION=True,
    SENTRY_DSN='',
)
def test_v120_production_readiness_flags_missing_error_tracking_settings():
    payload = get_platform_production_readiness()
    error_tracking_check = next(check for check in payload['checks'] if check['key'] == 'error_tracking_production_config')

    assert error_tracking_check['status'] == 'critical'
    assert 'SENTRY_DSN' in error_tracking_check['unsafe_flags']


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
    REST_FRAMEWORK={
        "DEFAULT_THROTTLE_RATES": {
            "auth_login": "10/minute",
            "auth_register": "20/hour",
            "auth_refresh": "60/minute",
            "auth_logout": "300/minute",
        },
    },
)
def test_v120_production_readiness_flags_unsafe_auth_logout_throttle():
    payload = get_platform_production_readiness()
    logout_check = next(check for check in payload['checks'] if check['key'] == 'auth_logout_throttle')

    assert logout_check['status'] == 'critical'
    assert logout_check['configured_rate'] == '300/minute'


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


@pytest.mark.django_db
@override_settings(
    IS_PRODUCTION=True,
    DATABASES={
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": "db.sqlite3",
        },
    },
)
def test_v120_production_readiness_flags_sqlite_in_production():
    payload = get_platform_production_readiness()
    database_check = next(check for check in payload['checks'] if check['key'] == 'production_database_backend')

    assert database_check['status'] == 'critical'
    assert 'sqlite' in database_check['engine']


@pytest.mark.django_db
@override_settings(
    IS_PRODUCTION=True,
    CSRF_TRUSTED_ORIGINS=['http://trainerhub.example.com'],
    CORS_ALLOWED_ORIGINS=['https://trainerhub.example.com'],
)
def test_v120_production_readiness_flags_http_csrf_origin_in_production():
    payload = get_platform_production_readiness()
    origin_check = next(check for check in payload['checks'] if check['key'] == 'production_origin_security')

    assert origin_check['status'] == 'critical'
    assert 'CSRF_TRUSTED_ORIGINS_HTTP' in origin_check['unsafe_flags']
