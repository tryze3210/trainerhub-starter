from apps.runtime import services as runtime_services
from apps.ops import services as ops_services


def test_runtime_and_ops_contracts_connect():
    health = runtime_services.get_health_status()
    diagnostics = ops_services.get_diagnostics_snapshot()
    assert health['service']
    assert 'checks' in diagnostics
