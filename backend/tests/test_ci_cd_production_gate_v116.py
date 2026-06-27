import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_v116_production_gate_script_contains_required_checks():
    script = _read("scripts/ci/production_gate.sh")

    required_fragments = [
        "python -m compileall backend",
        "python manage.py check",
        "python manage.py check --deploy --fail-level WARNING",
        "python manage.py makemigrations --check --dry-run",
        "pytest",
        "pytest tests/contracts",
        "python manage.py check_production_readiness --json --fail-on-degraded",
        "python -m pip check",
        "npm run typecheck",
        "npm run build",
        "npm run test:contracts",
        "npm audit --audit-level=high",
    ]
    for fragment in required_fragments:
        assert fragment in script


def test_v116_production_gate_script_is_executable():
    path = ROOT / "scripts/ci/production_gate.sh"

    assert path.exists()
    assert os.access(path, os.X_OK)


def test_v116_ci_workflow_requires_production_gate():
    workflow = _read(".github/workflows/ci.yml")

    assert "production-gate:" in workflow
    assert "needs: [backend-quality, frontend-build, launch-hardening]" in workflow
    assert "bash scripts/ci/production_gate.sh" in workflow


def test_v116_launch_gate_includes_production_gate_contract_test():
    script = _read("scripts/ci/launch_gate.sh")

    assert "tests/test_ci_cd_production_gate_v116.py" in script
