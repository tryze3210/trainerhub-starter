from apps.runtime import services


def test_health_contract():
    payload = services.get_health_status()
    assert payload['status'] in {'ok', 'degraded'}
    assert 'service' in payload


def test_readiness_contract():
    payload = services.get_readiness_status()
    assert 'checks' in payload
    assert isinstance(payload['checks'], list)
