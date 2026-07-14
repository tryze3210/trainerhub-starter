from django.test import override_settings

from apps.runtime import services as runtime_services
from apps.ops import services as ops_services


def test_runtime_and_ops_contracts_connect():
    health = runtime_services.get_health_status()
    diagnostics = ops_services.get_diagnostics_snapshot()
    assert health['service']
    assert 'checks' in diagnostics


def test_ops_diagnostics_reports_object_storage_configuration():
    diagnostics = ops_services.get_diagnostics_snapshot()
    storage_check = next(item for item in diagnostics['checks'] if item['key'] == 'object_storage_signer')
    assert storage_check['status'] == 'warning'
    assert 'scaffold' not in storage_check['message']

    with override_settings(
        VK_S3_ENDPOINT_URL='https://s3.example.test',
        VK_S3_ACCESS_KEY_ID='access-key',
        VK_S3_SECRET_ACCESS_KEY='secret-key',
    ):
        configured = ops_services.get_diagnostics_snapshot()

    configured_storage_check = next(item for item in configured['checks'] if item['key'] == 'object_storage_signer')
    assert configured_storage_check['status'] == 'ok'
