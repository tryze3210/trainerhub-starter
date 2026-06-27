from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from django.conf import settings


@dataclass(frozen=True)
class RunbookSpec:
    key: str
    title: str
    filename: str
    incident_type: str
    severity: str = "high"


REQUIRED_RUNBOOKS = [
    RunbookSpec("failed_payment_webhook", "Failed payment webhook", "failed-payment-webhook.md", "payments"),
    RunbookSpec("wrong_entitlement", "Wrong entitlement", "wrong-entitlement.md", "entitlements"),
    RunbookSpec("payout_mismatch", "Payout mismatch", "payout-mismatch.md", "payouts"),
    RunbookSpec("refund_conflict", "Refund conflict", "refund-conflict.md", "refunds"),
    RunbookSpec("database_restore", "Database restore", "database-restore.md", "infrastructure", "critical"),
    RunbookSpec("deployment_rollback", "Deployment rollback", "deployment-rollback.md", "deployment", "critical"),
]


def _runbook_dir() -> Path:
    return Path(settings.BASE_DIR) / "ops" / "runbooks"


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def get_ops_runbook_index(*, include_content: bool = False) -> dict[str, Any]:
    root = _runbook_dir()
    items = []
    missing = []
    for spec in REQUIRED_RUNBOOKS:
        path = root / spec.filename
        exists = path.exists()
        content = _read_text(path) if include_content and exists else ""
        item = {
            "key": spec.key,
            "title": spec.title,
            "incident_type": spec.incident_type,
            "severity": spec.severity,
            "path": str(path.relative_to(Path(settings.BASE_DIR))),
            "exists": exists,
            "sections": [line[3:].strip() for line in content.splitlines() if line.startswith("## ")] if content else [],
        }
        if include_content:
            item["content"] = content
        items.append(item)
        if not exists:
            missing.append(spec.key)
    return {
        "status": "ready" if not missing else "missing_runbooks",
        "total": len(items),
        "missing": missing,
        "runbooks": items,
    }


def get_ops_runbook(*, key: str) -> dict[str, Any]:
    index = get_ops_runbook_index(include_content=True)
    for item in index["runbooks"]:
        if item["key"] == key:
            return item
    raise KeyError(key)
