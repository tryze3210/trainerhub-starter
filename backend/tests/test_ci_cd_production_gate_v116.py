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
        '"$PYTHON_BIN" -m pytest tests/test_error_tracking_contract.py',
        '"$PYTHON_BIN" -m pytest',
        '"$PYTHON_BIN" -m pytest tests/contracts',
        '"$PYTHON_BIN" manage.py check_production_readiness --summary-only --fail-on-degraded',
        '"$PYTHON_BIN" -m pip check',
        'bash "$ROOT_DIR/scripts/quality/frontend_check.sh"',
        "npm audit --audit-level=high",
    ]
    for fragment in required_fragments:
        assert fragment in script


def test_v116_production_gate_uses_https_only_origin_defaults():
    script = _read("scripts/ci/production_gate.sh")

    assert 'APP_ENV="${APP_ENV:-production}"' in script
    assert 'API_BASE_URL="${API_BASE_URL:-https://api.trainerhub.local}"' in script
    assert 'FRONTEND_BASE_URL="${FRONTEND_BASE_URL:-https://trainerhub.local}"' in script
    assert 'REDIS_URL="${REDIS_URL:-redis://redis:6379/0}"' in script
    assert 'CACHE_URL="${CACHE_URL:-redis://redis:6379/0}"' in script
    assert 'CELERY_BROKER_URL="${CELERY_BROKER_URL:-redis://redis:6379/1}"' in script
    assert 'CELERY_RESULT_BACKEND="${CELERY_RESULT_BACKEND:-redis://redis:6379/2}"' in script
    assert 'CELERY_TASK_ALWAYS_EAGER="${CELERY_TASK_ALWAYS_EAGER:-0}"' in script
    assert 'SENTRY_DSN="${SENTRY_DSN:-https://public@example.ingest.sentry.io/1}"' in script
    assert 'VK_S3_ENDPOINT_URL="${VK_S3_ENDPOINT_URL:-$VK_CLOUD_ENDPOINT}"' in script
    assert 'VK_S3_ACCESS_KEY_ID="${VK_S3_ACCESS_KEY_ID:-$VK_CLOUD_ACCESS_KEY}"' in script
    assert 'VK_S3_SECRET_ACCESS_KEY="${VK_S3_SECRET_ACCESS_KEY:-$VK_CLOUD_SECRET_KEY}"' in script
    assert 'VK_PRIVATE_BUCKET="${VK_PRIVATE_BUCKET:-trainerhub-production-gate-private}"' in script
    assert 'VK_PUBLIC_BUCKET="${VK_PUBLIC_BUCKET:-trainerhub-production-gate-public}"' in script
    assert 'EMAIL_BACKEND="${EMAIL_BACKEND:-django.core.mail.backends.smtp.EmailBackend}"' in script
    assert 'DEFAULT_FROM_EMAIL="${DEFAULT_FROM_EMAIL:-TrainerHub <no-reply@trainerhub.local>}"' in script
    assert 'EMAIL_HOST="${EMAIL_HOST:-smtp.trainerhub.local}"' in script
    assert 'CSRF_TRUSTED_ORIGINS="${CSRF_TRUSTED_ORIGINS:-https://trainerhub.local}"' in script
    assert 'CORS_ALLOWED_ORIGINS="${CORS_ALLOWED_ORIGINS:-https://trainerhub.local}"' in script
    assert 'http://localhost' not in script


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
