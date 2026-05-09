from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from django.db.models import Count, DecimalField, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.utils import timezone

from apps.payouts.models import BalanceEntry, PayoutRequest, TrainerWallet
from apps.payouts.services import ACTIVE_PAYOUT_STATUSES, PayoutService

try:  # Projection code exists in the current project, but readiness must stay import-safe.
    from apps.payouts.projections import payout_revenue_projection_service
except Exception:  # pragma: no cover - defensive guard for partial local patch states.
    payout_revenue_projection_service = None

ZERO = Decimal("0.00")
MONEY_FIELD = DecimalField(max_digits=14, decimal_places=2)


@dataclass(frozen=True)
class PayoutReadinessOptions:
    include_projection: bool = True
    include_reconciliation: bool = True
    include_recommendations: bool = True


def _money(value: Decimal | None) -> Decimal:
    return value if value is not None else ZERO


def _sum_decimal(queryset, field: str = "amount") -> Decimal:
    return _money(
        queryset.aggregate(
            total=Coalesce(Sum(field), Value(ZERO), output_field=MONEY_FIELD)
        )["total"]
    )


def _status_counts() -> list[dict[str, Any]]:
    rows = (
        PayoutRequest.objects.values("status", "currency")
        .annotate(count=Count("id"), amount=Coalesce(Sum("amount"), Value(ZERO), output_field=MONEY_FIELD))
        .order_by("status", "currency")
    )
    return [
        {
            "status": row["status"],
            "currency": row["currency"],
            "count": row["count"],
            "amount": row["amount"],
        }
        for row in rows
    ]


def _ledger_counts() -> list[dict[str, Any]]:
    rows = (
        BalanceEntry.objects.values("entry_type", "direction", "currency", "status")
        .annotate(count=Count("id"), amount=Coalesce(Sum("amount"), Value(ZERO), output_field=MONEY_FIELD))
        .order_by("entry_type", "direction", "currency", "status")
    )
    return [
        {
            "entry_type": row["entry_type"],
            "direction": row["direction"],
            "currency": row["currency"],
            "status": row["status"],
            "count": row["count"],
            "amount": row["amount"],
        }
        for row in rows
    ]


def _wallet_totals() -> dict[str, Any]:
    aggregate = TrainerWallet.objects.aggregate(
        trainers_count=Count("id"),
        available_amount=Coalesce(Sum("available_amount"), Value(ZERO), output_field=MONEY_FIELD),
        locked_amount=Coalesce(Sum("locked_amount"), Value(ZERO), output_field=MONEY_FIELD),
        pending_amount=Coalesce(Sum("pending_amount"), Value(ZERO), output_field=MONEY_FIELD),
    )
    return {
        "trainers_count": aggregate["trainers_count"],
        "available_amount": aggregate["available_amount"],
        "locked_amount": aggregate["locked_amount"],
        "reserved_amount": aggregate["locked_amount"],
        "pending_amount": aggregate["pending_amount"],
    }


def _risk_hold_summary() -> dict[str, Any]:
    holds = BalanceEntry.objects.filter(
        entry_type=BalanceEntry.EntryType.RISK_HOLD,
        source_type="payment_dispute_hold",
    )
    releases = BalanceEntry.objects.filter(entry_type=BalanceEntry.EntryType.RISK_HOLD_RELEASE)
    consumed = BalanceEntry.objects.filter(entry_type=BalanceEntry.EntryType.RISK_HOLD_CONSUMED)
    active_amount = _sum_decimal(holds) - _sum_decimal(releases) - _sum_decimal(consumed)
    if active_amount < ZERO:
        active_amount = ZERO
    return {
        "hold_count": holds.count(),
        "release_count": releases.count(),
        "consumed_count": consumed.count(),
        "hold_amount": _sum_decimal(holds),
        "released_amount": _sum_decimal(releases),
        "consumed_amount": _sum_decimal(consumed),
        "active_hold_amount": active_amount,
    }


def _transition_matrix() -> dict[str, list[str]]:
    return {
        PayoutRequest.Status.REQUESTED: ["approve", "reject"],
        PayoutRequest.Status.PENDING: ["approve", "reject"],
        PayoutRequest.Status.APPROVED: ["processing", "reject"],
        PayoutRequest.Status.PROCESSING: ["paid"],
        PayoutRequest.Status.PAID: [],
        PayoutRequest.Status.REJECTED: [],
    }


def _api_surface() -> dict[str, Any]:
    return {
        "trainer": [
            "GET /api/v1/payouts/my/balance/",
            "GET /api/v1/payouts/my/",
            "GET /api/v1/payouts/my/{id}/",
            "POST /api/v1/payouts/my/request/",
        ],
        "admin": [
            "GET /api/v1/payouts/admin/overview/",
            "GET /api/v1/payouts/admin/",
            "GET /api/v1/payouts/admin/{id}/",
            "POST /api/v1/payouts/admin/{id}/transition/",
            "POST /api/v1/payouts/admin/{id}/approve/",
            "POST /api/v1/payouts/admin/{id}/processing/",
            "POST /api/v1/payouts/admin/{id}/mark-paid/",
            "POST /api/v1/payouts/admin/{id}/reject/",
            "POST /api/v1/payouts/admin/bulk-transition/",
            "GET /api/v1/payouts/admin/projection-health/",
            "POST /api/v1/payouts/admin/project-outbox/",
            "GET /api/v1/payouts/admin/risk-holds/",
            "GET /api/v1/payouts/admin/risk-holds/summary/",
            "POST /api/v1/payouts/admin/risk-holds/release/",
            "GET /api/v1/payouts/admin/reconciliation/",
            "POST /api/v1/payouts/admin/reconciliation/repair/",
            "GET /api/v1/payouts/admin/readiness/",
        ],
        "required_actions": ["approve", "processing", "paid", "reject"],
        "bulk_actions": ["approve", "processing", "paid", "reject"],
    }


def _projection_payload() -> dict[str, Any]:
    if payout_revenue_projection_service is None:
        return {
            "status": "unavailable",
            "consumer": "payout_revenue_projection",
            "error": "Payout revenue projection service is not importable.",
        }
    try:
        payload = payout_revenue_projection_service.projection_health()
        return {"status": payload.get("status", "unknown"), **payload}
    except Exception as exc:  # pragma: no cover - defensive guard for broken partial installs.
        return {"status": "failed", "error": str(exc)}


def _reconciliation_payload() -> dict[str, Any]:
    try:
        payload = PayoutService.build_reconciliation_report()
        return {
            "status": payload.get("status", "unknown"),
            "issue_count": payload.get("issue_count", len(payload.get("issues", []))),
            "active_statuses": payload.get("active_statuses", []),
            "issues": payload.get("issues", [])[:25],
            "checked_at": payload.get("checked_at"),
        }
    except Exception as exc:  # pragma: no cover - defensive guard for broken partial installs.
        return {"status": "failed", "issue_count": 1, "issues": [{"message": str(exc)}]}


def _checks(*, wallets: dict[str, Any], reconciliation: dict[str, Any], projection: dict[str, Any], risk_holds: dict[str, Any]) -> list[dict[str, Any]]:
    active_payouts = PayoutRequest.objects.filter(status__in=ACTIVE_PAYOUT_STATUSES)
    active_amount = _sum_decimal(active_payouts)
    negative_wallets = TrainerWallet.objects.filter(Q(available_amount__lt=ZERO) | Q(locked_amount__lt=ZERO)).count()
    stuck_processing = PayoutRequest.objects.filter(
        status=PayoutRequest.Status.PROCESSING,
        updated_at__lt=timezone.now() - timezone.timedelta(days=7),
    ).count()
    reconciliation_issue_count = int(reconciliation.get("issue_count") or 0)
    projection_status = projection.get("status") or "unknown"

    checks: list[dict[str, Any]] = []
    checks.append(
        {
            "code": "payout_transition_surface",
            "status": "ok",
            "severity": "info",
            "message": "Admin payout transition endpoints and workflow actions are declared.",
            "details": {"transition_matrix": _transition_matrix()},
        }
    )
    checks.append(
        {
            "code": "wallet_non_negative_balances",
            "status": "ok" if negative_wallets == 0 else "critical",
            "severity": "critical" if negative_wallets else "info",
            "message": "Trainer wallets must not have negative available or locked balances.",
            "details": {"negative_wallet_count": negative_wallets, **wallets},
        }
    )
    checks.append(
        {
            "code": "active_payout_exposure",
            "status": "ok",
            "severity": "info",
            "message": "Current active payout exposure is measurable.",
            "details": {"active_payout_count": active_payouts.count(), "active_payout_amount": active_amount},
        }
    )
    checks.append(
        {
            "code": "stuck_processing_payouts",
            "status": "ok" if stuck_processing == 0 else "warning",
            "severity": "warning" if stuck_processing else "info",
            "message": "Processing payouts older than seven days require admin review.",
            "details": {"stuck_processing_count": stuck_processing},
        }
    )
    checks.append(
        {
            "code": "payout_reconciliation",
            "status": "ok" if reconciliation_issue_count == 0 else "degraded",
            "severity": "high" if reconciliation_issue_count else "info",
            "message": "Wallet locked balances should match active payout requests.",
            "details": reconciliation,
        }
    )
    checks.append(
        {
            "code": "payout_projection_health",
            "status": "ok" if projection_status in {"healthy", "ok", "idle", "unknown"} else "degraded",
            "severity": "warning" if projection_status not in {"healthy", "ok", "idle", "unknown"} else "info",
            "message": "Payout revenue projection health is available for admin review.",
            "details": projection,
        }
    )
    checks.append(
        {
            "code": "risk_hold_visibility",
            "status": "ok",
            "severity": "info",
            "message": "Payment dispute risk-hold exposure is visible to admins.",
            "details": risk_holds,
        }
    )
    return checks


def _overall_status(checks: list[dict[str, Any]]) -> str:
    statuses = {item["status"] for item in checks}
    severities = {item["severity"] for item in checks if item["status"] != "ok"}
    if "critical" in statuses or "critical" in severities:
        return "critical"
    if statuses & {"degraded", "warning", "failed"} or severities & {"high", "warning"}:
        return "degraded"
    return "ok"


def _recommendations(checks: list[dict[str, Any]]) -> list[str]:
    failed = [item for item in checks if item["status"] != "ok"]
    if not failed:
        return [
            "Keep payout readiness in the admin smoke checklist after payout API changes.",
            "Run payout reconciliation dry-run before bulk payout transitions.",
        ]
    messages: list[str] = []
    for item in failed:
        if item["code"] == "wallet_non_negative_balances":
            messages.append("Review negative wallets before approving or marking payouts as paid.")
        elif item["code"] == "stuck_processing_payouts":
            messages.append("Investigate processing payouts older than seven days and add external references before marking paid.")
        elif item["code"] == "payout_reconciliation":
            messages.append("Run payout reconciliation dry-run and apply repair only after reviewing generated actions.")
        elif item["code"] == "payout_projection_health":
            messages.append("Run project-outbox and inspect failed payout projection inbox messages.")
    return messages


def build_admin_payout_readiness(*, options: PayoutReadinessOptions | None = None) -> dict[str, Any]:
    opts = options or PayoutReadinessOptions()
    wallets = _wallet_totals()
    risk_holds = _risk_hold_summary()
    projection = _projection_payload() if opts.include_projection else {"status": "skipped"}
    reconciliation = _reconciliation_payload() if opts.include_reconciliation else {"status": "skipped", "issue_count": 0}
    checks = _checks(wallets=wallets, reconciliation=reconciliation, projection=projection, risk_holds=risk_holds)
    status = _overall_status(checks)
    warning_count = sum(1 for item in checks if item["status"] in {"warning", "degraded"})
    critical_count = sum(1 for item in checks if item["status"] == "critical" or item["severity"] == "critical")

    payload: dict[str, Any] = {
        "status": status,
        "generated_at": timezone.now().isoformat(),
        "summary": {
            "checks_total": len(checks),
            "ok_count": sum(1 for item in checks if item["status"] == "ok"),
            "warning_count": warning_count,
            "critical_count": critical_count,
            "wallets": wallets,
            "active_payouts": {
                "count": PayoutRequest.objects.filter(status__in=ACTIVE_PAYOUT_STATUSES).count(),
                "amount": _sum_decimal(PayoutRequest.objects.filter(status__in=ACTIVE_PAYOUT_STATUSES)),
            },
            "risk_holds": risk_holds,
            "reconciliation_issue_count": int(reconciliation.get("issue_count") or 0),
        },
        "api_surface": _api_surface(),
        "workflow": {
            "active_statuses": sorted(str(item) for item in ACTIVE_PAYOUT_STATUSES),
            "terminal_statuses": [PayoutRequest.Status.PAID, PayoutRequest.Status.REJECTED],
            "transition_matrix": _transition_matrix(),
            "reject_reason_required": True,
            "external_reference_supported": True,
            "bulk_transition_supported": True,
            "risk_hold_release_supported": True,
            "reconciliation_repair_supported": True,
        },
        "checks": checks,
        "status_buckets": _status_counts(),
        "ledger_buckets": _ledger_counts(),
        "projection": projection,
        "reconciliation": reconciliation,
    }
    if opts.include_recommendations:
        payload["recommendations"] = _recommendations(checks)
    return payload
