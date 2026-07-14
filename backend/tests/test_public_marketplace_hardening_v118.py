from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_public_marketplace_hardening_endpoints_are_registered():
    urls_source = (ROOT / 'apps' / 'public_catalog' / 'api' / 'urls.py').read_text()

    assert "name='public-marketplace-home'" in urls_source
    assert "name='public-marketplace-content-landing'" in urls_source
    assert "name='public-marketplace-trainer-landing'" in urls_source


def test_public_marketplace_payload_contains_seo_pricing_reviews_and_checkout_cta():
    services_source = (ROOT / 'apps' / 'public_catalog' / 'services.py').read_text()

    assert 'PUBLIC_MARKETPLACE_SEO' in services_source
    assert 'build_marketplace_home' in services_source
    assert 'build_content_landing' in services_source
    assert 'build_trainer_landing' in services_source
    assert "'canonical_path'" in services_source
    assert "'pricing'" in services_source
    assert "'reviews'" in services_source
    assert "'checkout_cta'" in services_source
    assert "'requires_auth': True" in services_source


def test_production_readiness_tracks_public_marketplace_v118():
    readiness_source = (ROOT / 'apps' / 'ops' / 'production_readiness.py').read_text()

    assert "LEGACY_CONTRACT_VERSIONS = {'public_marketplace': 'v118'}" in readiness_source
    assert 'public_marketplace_home' in readiness_source
    assert 'public_marketplace_content_landing' in readiness_source
    assert 'public_marketplace_trainer_landing' in readiness_source
    assert 'test_public_marketplace_hardening_v118.py' in readiness_source
