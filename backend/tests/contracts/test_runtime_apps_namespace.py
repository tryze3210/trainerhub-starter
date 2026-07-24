from pathlib import Path


def test_root_apps_namespace_is_not_importable_runtime_package():
    repo_root = Path(__file__).resolve().parents[3]

    assert not (repo_root / 'apps' / '__init__.py').exists()
    assert (repo_root / 'backend' / 'apps' / '__init__.py').exists()
    assert (repo_root / 'legacy' / 'root_apps' / '__init__.py').exists()
