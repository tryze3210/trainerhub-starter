from pathlib import Path

from apps.ops.launch_candidate import get_launch_candidate_pack, get_project_version


ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = Path(__file__).resolve().parents[1]


def test_launch_candidate_pack_contains_release_contract_sections():
    payload = get_launch_candidate_pack()

    assert payload["version"] == "v119"
    assert payload["project_version"] == "v167.0"
    assert payload["scope"] == "launch candidate"
    assert payload["status"] == "ok"
    assert payload["release_notes"]
    assert payload["smoke_checklist"]
    assert payload["production_env_checklist"]
    assert payload["known_limitations"]
    assert payload["release_decision"]["next_step"] == "v120 Production Launch Pack"


def test_project_version_is_read_from_version_file():
    assert get_project_version(repo_root=ROOT) == "v167.0"


def test_launch_candidate_required_artifacts_exist():
    payload = get_launch_candidate_pack()

    assert payload["missing_artifacts"] == []
    required_paths = {item["path"] for item in payload["required_artifacts"]}
    assert "VERSION" in required_paths
    assert "docs/launch/launch_candidate_v119.md" in required_paths
    assert "scripts/ci/production_gate.sh" in required_paths


def test_launch_candidate_api_and_readiness_contracts_are_registered():
    urls_source = (BACKEND_ROOT / "apps" / "ops" / "api" / "urls.py").read_text()
    views_source = (BACKEND_ROOT / "apps" / "ops" / "api" / "views.py").read_text()
    readiness_source = (BACKEND_ROOT / "apps" / "ops" / "production_readiness.py").read_text()

    assert "name='ops-admin-launch-candidate'" in urls_source
    assert "AdminLaunchCandidateView" in views_source
    assert "'version': 'v120'" in readiness_source
    assert "launch_candidate_pack" in readiness_source
    assert "test_launch_candidate_v119.py" in readiness_source
