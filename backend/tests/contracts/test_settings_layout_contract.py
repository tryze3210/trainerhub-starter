from pathlib import Path


def test_django_settings_layout_uses_canonical_package_modules():
    repo_root = Path(__file__).resolve().parents[3]
    config_dir = repo_root / 'backend' / 'config'

    assert (config_dir / 'settings' / 'base.py').exists()
    assert (config_dir / 'settings' / 'local.py').exists()
    assert (config_dir / 'settings' / 'production.py').exists()
    assert (config_dir / 'settings' / 'test.py').exists()

    legacy_settings = (config_dir / 'settings.py').read_text().strip()
    legacy_test_settings = (config_dir / 'settings_test.py').read_text().strip()

    assert legacy_settings == 'from config.settings.base import *  # noqa: F401,F403'
    assert legacy_test_settings == 'from config.settings.test import *  # noqa: F401,F403'

