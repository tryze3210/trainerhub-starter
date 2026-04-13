from scripts.bootstrap.seed_demo import build_demo_seed_payload


def test_demo_seed_payload_contains_core_sections():
    payload = build_demo_seed_payload()
    assert 'accounts' in payload
    assert 'trainers' in payload
    assert 'catalog' in payload
