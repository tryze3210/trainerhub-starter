from __future__ import annotations

import re
from pathlib import Path


APP_ROOT = Path(__file__).resolve().parents[2] / "apps"
ALLOWED_STATUS_WRITERS = {
    Path("payouts/services.py"),
}

DIRECT_STATUS_MUTATION_PATTERNS = (
    re.compile(r"\.status\s*=\s*PayoutRequest\.Status\."),
    re.compile(r"\.update\([^)]*status\s*=\s*PayoutRequest\.Status\.", re.DOTALL),
)


def test_payout_request_status_is_mutated_only_by_payout_service():
    offenders: list[str] = []
    for path in sorted(APP_ROOT.rglob("*.py")):
        relative = path.relative_to(APP_ROOT)
        if "migrations" in relative.parts or relative in ALLOWED_STATUS_WRITERS:
            continue
        source = path.read_text(encoding="utf-8")
        if any(pattern.search(source) for pattern in DIRECT_STATUS_MUTATION_PATTERNS):
            offenders.append(str(relative))

    assert offenders == []
