from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_VERSION_FILE = "VERSION"
LAUNCH_CANDIDATE_VERSION = "v119"


SMOKE_CHECKLIST = [
    {
        "key": "backend_quality",
        "title": "Backend quality gate",
        "command": "cd backend && python manage.py check && python manage.py makemigrations --check --dry-run && pytest",
    },
    {
        "key": "frontend_build",
        "title": "Frontend typecheck and build",
        "command": "cd frontend && npm run typecheck && npm run build",
    },
    {
        "key": "production_readiness",
        "title": "Production readiness gate",
        "command": "cd backend && python manage.py check_production_readiness --json --fail-on-degraded",
    },
    {
        "key": "launch_gate",
        "title": "Launch gate",
        "command": "bash scripts/ci/launch_gate.sh",
    },
    {
        "key": "production_gate",
        "title": "Production CI/CD gate",
        "command": "bash scripts/ci/production_gate.sh",
    },
    {
        "key": "demo_seed",
        "title": "Demo seed scenarios",
        "command": "bash scripts/deploy/migrate.sh && python scripts/bootstrap/seed_demo.py",
    },
]


PRODUCTION_ENV_CHECKLIST = [
    {"key": "database_url", "title": "DATABASE_URL points to production database", "required": True},
    {"key": "secret_key", "title": "DJANGO_SECRET_KEY is set and not shared with local/dev", "required": True},
    {"key": "allowed_hosts", "title": "ALLOWED_HOSTS includes production domains", "required": True},
    {"key": "cors_csrf", "title": "CORS and CSRF trusted origins match production frontend domains", "required": True},
    {"key": "payment_webhooks", "title": "Payment provider webhook secrets and endpoints are configured", "required": True},
    {"key": "object_storage", "title": "Media/video object storage credentials are configured", "required": True},
    {"key": "email_notifications", "title": "Email/SMS/push notification providers are configured", "required": True},
    {"key": "workers", "title": "Background workers and schedulers are deployed", "required": True},
    {"key": "observability", "title": "Health checks, alerts and logs are connected to production monitoring", "required": True},
    {"key": "backups", "title": "Database backup and restore procedure has been tested", "required": True},
]


KNOWN_LIMITATIONS = [
    {
        "key": "local_dependency_gap",
        "severity": "environment",
        "description": "Some local backend test runs require the full Django/DRF dependency set in the active interpreter.",
    },
    {
        "key": "provider_live_validation",
        "severity": "release",
        "description": "Payment provider live credentials and webhook delivery must be validated in staging before production traffic.",
    },
    {
        "key": "video_cdn_validation",
        "severity": "release",
        "description": "Signed video URL delivery and anti-leeching should be validated against the chosen production CDN/storage.",
    },
    {
        "key": "legal_documents_final_copy",
        "severity": "business",
        "description": "Terms, privacy and refund policy text must be approved before enabling real purchases.",
    },
]


RELEASE_NOTES = [
    {
        "key": "payouts",
        "title": "Payout production readiness",
        "summary": "Integrity snapshots, repair preview/execution, repair audit UI, exports and ops dashboard are in place.",
        "versions": "v70-v77",
    },
    {
        "key": "payments_orders_entitlements",
        "title": "Payments, orders and entitlements",
        "summary": "Webhook hardening, idempotency, entitlement activation, refunds, revocation and reconciliation are covered.",
        "versions": "v80-v85",
    },
    {
        "key": "admin_billing_subscriptions",
        "title": "Admin billing and subscriptions",
        "summary": "Payment admin UI, customer billing UI, trainer sales, subscription lifecycle, access guard and notifications are covered.",
        "versions": "v86-v91",
    },
    {
        "key": "crm_booking_attendance",
        "title": "CRM, booking and attendance",
        "summary": "Customer CRM, trainer schedules, booking limits, waitlist and attendance/check-in flows are in place.",
        "versions": "v92-v95",
    },
    {
        "key": "learning_content",
        "title": "Content, learning and messaging",
        "summary": "Course/program builder, access runtime, video delivery, learning area, progress, homework, reviews and messaging are in place.",
        "versions": "v97-v105",
    },
    {
        "key": "launch_ops",
        "title": "Launch operations hardening",
        "summary": "Role matrix, tenant isolation, global search, support console, chargebacks, finance docs, legal compliance, observability, runbooks, CI gate, demo seed and public marketplace contracts are in place.",
        "versions": "v106-v118",
    },
]


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def get_project_version(*, repo_root: Path | None = None) -> str:
    root = repo_root or _repo_root()
    version_file = root / PROJECT_VERSION_FILE
    if not version_file.exists():
        return LAUNCH_CANDIDATE_VERSION
    return version_file.read_text(encoding="utf-8").strip() or LAUNCH_CANDIDATE_VERSION


def _required_artifacts(repo_root: Path) -> list[dict[str, Any]]:
    paths = [
        "README.md",
        "MANIFEST.md",
        "BUILD_REPORT.md",
        "VERSION",
        "scripts/ci/launch_gate.sh",
        "scripts/ci/production_gate.sh",
        "scripts/bootstrap/seed_demo.py",
        "docs/launch/launch_candidate_v119.md",
    ]
    return [
        {
            "path": path,
            "exists": (repo_root / path).exists(),
        }
        for path in paths
    ]


def get_launch_candidate_pack(*, include_artifacts: bool = True) -> dict[str, Any]:
    repo_root = _repo_root()
    artifacts = _required_artifacts(repo_root) if include_artifacts else []
    missing = [item["path"] for item in artifacts if not item["exists"]]
    return {
        "status": "ok" if not missing else "degraded",
        "version": LAUNCH_CANDIDATE_VERSION,
        "project_version": get_project_version(repo_root=repo_root),
        "generated_at": datetime.now(timezone.utc),
        "scope": "launch candidate",
        "release_notes": RELEASE_NOTES,
        "smoke_checklist": SMOKE_CHECKLIST,
        "production_env_checklist": PRODUCTION_ENV_CHECKLIST,
        "known_limitations": KNOWN_LIMITATIONS,
        "required_artifacts": artifacts,
        "missing_artifacts": missing,
        "release_decision": {
            "candidate": "v119",
            "next_step": "v120 Production Launch Pack",
            "ship_condition": "CI green, production readiness ok, staging webhook/video/legal validation complete.",
        },
    }
