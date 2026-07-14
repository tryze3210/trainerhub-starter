from pathlib import Path

from apps.ops.production_launch_pack import get_production_launch_pack


ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = Path(__file__).resolve().parents[1]


def test_production_launch_pack_contains_all_required_docs():
    payload = get_production_launch_pack()

    assert payload["version"] == "v120"
    assert payload["project_version"] == "v167.0"
    assert payload["status"] == "ready"
    assert payload["missing_documents"] == []
    assert {document["key"] for document in payload["documents"]} == {
        "deploy",
        "backup",
        "monitoring",
        "admin",
        "trainer",
        "student",
        "index",
    }


def test_production_launch_pack_contains_final_gates_and_handoffs():
    payload = get_production_launch_pack()

    gate_keys = {gate["key"] for gate in payload["final_gates"]}
    handoff_roles = {handoff["role"] for handoff in payload["handoffs"]}
    assert {"production_gate", "launch_gate", "production_readiness", "demo_seed"}.issubset(gate_keys)
    assert {"admin", "support", "finance", "trainer", "student", "engineering"}.issubset(handoff_roles)
    assert payload["release_state"]["next_step"] == "production deployment"


def test_production_launch_pack_endpoint_and_readiness_contracts_are_registered():
    urls_source = (BACKEND_ROOT / "apps" / "ops" / "api" / "urls.py").read_text()
    views_source = (BACKEND_ROOT / "apps" / "ops" / "api" / "views.py").read_text()
    readiness_source = (BACKEND_ROOT / "apps" / "ops" / "production_readiness.py").read_text()

    assert "name='ops-admin-production-launch-pack'" in urls_source
    assert "AdminProductionLaunchPackView" in views_source
    assert "'version': 'v120'" in readiness_source
    assert "production_launch_pack" in readiness_source
    assert "test_production_launch_pack_v120.py" in readiness_source


def test_production_launch_pack_docs_exist_on_disk():
    expected = [
        "docs/launch/production/README.md",
        "docs/launch/production/deploy.md",
        "docs/launch/production/backup.md",
        "docs/launch/production/monitoring.md",
        "docs/launch/production/admin.md",
        "docs/launch/production/trainer.md",
        "docs/launch/production/student.md",
    ]

    assert all((ROOT / path).exists() for path in expected)
