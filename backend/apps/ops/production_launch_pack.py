from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PRODUCTION_LAUNCH_VERSION = "v120"
PROJECT_VERSION = "v167.0"


DOCUMENTS = [
    {
        "key": "deploy",
        "title": "Deploy docs",
        "path": "docs/launch/production/deploy.md",
        "audience": "engineering",
    },
    {
        "key": "backup",
        "title": "Backup docs",
        "path": "docs/launch/production/backup.md",
        "audience": "engineering",
    },
    {
        "key": "monitoring",
        "title": "Monitoring docs",
        "path": "docs/launch/production/monitoring.md",
        "audience": "ops",
    },
    {
        "key": "admin",
        "title": "Admin docs",
        "path": "docs/launch/production/admin.md",
        "audience": "admin/support/finance",
    },
    {
        "key": "trainer",
        "title": "Trainer docs",
        "path": "docs/launch/production/trainer.md",
        "audience": "trainer",
    },
    {
        "key": "student",
        "title": "Student docs",
        "path": "docs/launch/production/student.md",
        "audience": "student",
    },
    {
        "key": "index",
        "title": "Production launch pack index",
        "path": "docs/launch/production/README.md",
        "audience": "all",
    },
]


FINAL_GATES = [
    {"key": "production_gate", "command": "bash scripts/ci/production_gate.sh"},
    {"key": "launch_gate", "command": "bash scripts/ci/launch_gate.sh"},
    {
        "key": "production_readiness",
        "command": "cd backend && python manage.py check_production_readiness --json --fail-on-degraded",
    },
    {"key": "demo_seed", "command": "python scripts/bootstrap/seed_demo.py"},
]


HANDOFFS = [
    {"role": "admin", "docs": ["admin", "monitoring"], "primary_surface": "/admin/operations"},
    {"role": "support", "docs": ["admin", "monitoring"], "primary_surface": "/admin/operations"},
    {"role": "finance", "docs": ["admin", "backup"], "primary_surface": "/admin/payouts"},
    {"role": "trainer", "docs": ["trainer"], "primary_surface": "/trainer/dashboard"},
    {"role": "student", "docs": ["student"], "primary_surface": "/learning"},
    {"role": "engineering", "docs": ["deploy", "backup", "monitoring"], "primary_surface": "/api/v1/ops/admin/production-readiness/"},
]


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _version_text(repo_root: Path) -> str:
    path = repo_root / "VERSION"
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8").strip()


def _document_status(repo_root: Path, *, include_content: bool) -> list[dict[str, Any]]:
    rows = []
    for document in DOCUMENTS:
        path = repo_root / document["path"]
        row = {
            **document,
            "exists": path.exists(),
            "size": path.stat().st_size if path.exists() else 0,
        }
        if include_content:
            row["content"] = path.read_text(encoding="utf-8") if path.exists() else ""
        rows.append(row)
    return rows


def get_production_launch_pack(*, include_content: bool = False) -> dict[str, Any]:
    repo_root = _repo_root()
    documents = _document_status(repo_root, include_content=include_content)
    missing_documents = [item["path"] for item in documents if not item["exists"]]
    project_version = _version_text(repo_root)
    status = "ready" if not missing_documents and project_version == PROJECT_VERSION else "degraded"
    return {
        "status": status,
        "version": PRODUCTION_LAUNCH_VERSION,
        "project_version": project_version,
        "generated_at": datetime.now(timezone.utc),
        "scope": "production launch pack",
        "documents": documents,
        "missing_documents": missing_documents,
        "final_gates": FINAL_GATES,
        "handoffs": HANDOFFS,
        "release_state": {
            "previous_stage": "v119-launch-candidate",
            "current_stage": PROJECT_VERSION,
            "next_step": "production deployment",
            "ship_condition": "Production gate green, production readiness ok, staging validation complete.",
        },
    }
