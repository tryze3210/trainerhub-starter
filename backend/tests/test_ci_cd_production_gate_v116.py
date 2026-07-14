import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_v116_production_gate_script_contains_required_checks():
    script = _read("scripts/ci/production_gate.sh")

    required_fragments = [
        '"$PYTHON_BIN" -m compileall -q backend/apps backend/common backend/config backend/scripts backend/manage.py',
        '"$PYTHON_BIN" manage.py check',
        '"$PYTHON_BIN" manage.py check --deploy --fail-level WARNING',
        '"$PYTHON_BIN" manage.py makemigrations --check --dry-run',
        '"$PYTHON_BIN" -m pytest',
        '"$PYTHON_BIN" -m pytest tests/contracts',
        '"$PYTHON_BIN" manage.py check_production_readiness --summary-only --fail-on-degraded',
        '"$PYTHON_BIN" -m pip check',
        'bash "$ROOT_DIR/scripts/quality/frontend_check.sh"',
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
    assert "Run backend contract tests" in workflow
    assert "scripts/test/run_backend_contracts.sh" in workflow
    assert "bash scripts/ci/production_gate.sh" in workflow


def test_v116_launch_gate_includes_production_gate_contract_test():
    script = _read("scripts/ci/launch_gate.sh")

    assert "tests/test_auth_login_audit.py" in script
    assert "tests/test_ci_cd_production_gate_v116.py" in script
    assert 'bash "$ROOT_DIR/scripts/test/run_backend_contracts.sh"' in script
