from __future__ import annotations

import csv
import io
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Iterable

from django.db.models import Q
from django.http import HttpResponse
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit.services import AuditService
from apps.payouts.models import BalanceEntry, PayoutRequest
from apps.payouts.ops_selectors import build_payout_admin_ops_summary
from apps.payouts.services import PayoutService

EXPORT_LIMIT = 10_000


def _query_value(params, key: str) -> str:
    value = params.get(key, "")
    return str(value).strip() if value is not None else ""


def _positive_int(value: str, *, default: int, maximum: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return max(1, min(parsed, maximum))


def _money(value: Decimal | None) -> str:
    amount = value if value is not None else Decimal("0.00")
    return f"{amount.quantize(Decimal('0.01'))}"


def _apply_created_filters(queryset, params):
    created_from = _query_value(params, "created_from")
    created_to = _query_value(params, "created_to")
    if created_from:
        queryset = queryset.filter(created_at__gte=created_from)
    if created_to:
        queryset = queryset.filter(created_at__lte=created_to)
    return queryset


def _audit_context(*, request, export_type: str, filename: str, filters: dict, exported_rows: int, total_rows: int, limit: int) -> None:
    AuditService.log_admin_action(
        request=request,
        action="payouts.admin_ops.csv_export",
        target_type="payout_export",
        target_id=export_type,
        context={
            "export_type": export_type,
            "filename": filename,
            "filters": filters,
            "exported_rows": exported_rows,
            "total_rows": total_rows,
            "limit": limit,
            "truncated": total_rows > exported_rows,
        },
    )




def _json_safe(value: Any):
    if isinstance(value, Decimal):
        return _money(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    return value

def _csv_response(*, filename: str, header: list[str], rows: Iterable[list[str]]) -> HttpResponse:
    buffer = io.StringIO()
    buffer.write("\ufeff")
    writer = csv.writer(buffer)
    writer.writerow(header)
    writer.writerows(rows)

    response = HttpResponse(buffer.getvalue(), content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


class AdminPayoutOpsSummaryAPIView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        return Response(build_payout_admin_ops_summary(request.query_params))


class AdminPayoutOpsReconciliationSnapshotAPIView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        report = PayoutService.build_reconciliation_report()
        safe_report = _json_safe(report)
        return Response(
            {
                "generated_at": datetime.utcnow().isoformat() + "Z",
                "mode": "read_only_snapshot",
                "summary": {
                    "status": safe_report.get("status", "unknown"),
                    "issue_count": safe_report.get("issue_count", 0),
                    "checked_at": safe_report.get("checked_at", ""),
                },
                "snapshot": safe_report,
                "actions": {
                    "repair_performed": False,
                    "note": "This endpoint is read-only. It does not mutate payout requests, wallets or ledger entries.",
                },
            }
        )


class AdminPayoutOpsRequestsExportAPIView(APIView):
    permission_classes = [IsAdminUser]

    def get_queryset(self, request):
        queryset = PayoutRequest.objects.select_related("trainer", "trainer__user", "wallet").order_by("-created_at")
        params = request.query_params

        status = _query_value(params, "status")
        trainer_id = _query_value(params, "trainer_id")
        currency = _query_value(params, "currency")

        if status:
            if status == PayoutRequest.Status.PENDING:
                queryset = queryset.filter(status__in=[PayoutRequest.Status.PENDING, PayoutRequest.Status.REQUESTED])
            else:
                queryset = queryset.filter(status=status)
        if trainer_id:
            queryset = queryset.filter(Q(trainer__user_id=trainer_id) | Q(trainer_id=trainer_id))
        if currency:
            queryset = queryset.filter(currency=currency.upper())
        return _apply_created_filters(queryset, params)

    def get(self, request):
        limit = _positive_int(_query_value(request.query_params, "limit"), default=EXPORT_LIMIT, maximum=EXPORT_LIMIT)
        queryset = self.get_queryset(request)
        total_rows = queryset.count()
        payouts = list(queryset[:limit])
        filename = "payout_admin_requests_export.csv"

        rows = [
            [
                str(payout.id),
                str(payout.trainer_id),
                getattr(payout.trainer, "display_name", ""),
                payout.status,
                _money(payout.amount),
                payout.currency,
                payout.destination_masked,
                payout.created_at.isoformat(),
                payout.updated_at.isoformat(),
            ]
            for payout in payouts
        ]

        filters = {key: _query_value(request.query_params, key) for key in ["status", "trainer_id", "currency", "created_from", "created_to"]}
        _audit_context(
            request=request,
            export_type="requests",
            filename=filename,
            filters=filters,
            exported_rows=len(rows),
            total_rows=total_rows,
            limit=limit,
        )

        return _csv_response(
            filename=filename,
            header=["id", "trainer_id", "trainer_name", "status", "amount", "currency", "destination_masked", "created_at", "updated_at"],
            rows=rows,
        )


class AdminPayoutOpsLedgerExportAPIView(APIView):
    permission_classes = [IsAdminUser]

    def get_queryset(self, request):
        queryset = (
            BalanceEntry.objects.select_related("wallet", "wallet__trainer", "wallet__trainer__user")
            .order_by("-created_at")
        )
        params = request.query_params

        status = _query_value(params, "status")
        trainer_id = _query_value(params, "trainer_id")
        currency = _query_value(params, "currency")
        entry_type = _query_value(params, "entry_type")
        direction = _query_value(params, "direction")
        source_type = _query_value(params, "source_type")

        if status:
            queryset = queryset.filter(status=status)
        if trainer_id:
            queryset = queryset.filter(Q(wallet__trainer__user_id=trainer_id) | Q(wallet__trainer_id=trainer_id))
        if currency:
            queryset = queryset.filter(currency=currency.upper())
        if entry_type:
            queryset = queryset.filter(entry_type=entry_type)
        if direction:
            queryset = queryset.filter(direction=direction)
        if source_type:
            queryset = queryset.filter(source_type=source_type)
        return _apply_created_filters(queryset, params)

    def get(self, request):
        limit = _positive_int(_query_value(request.query_params, "limit"), default=EXPORT_LIMIT, maximum=EXPORT_LIMIT)
        queryset = self.get_queryset(request)
        total_rows = queryset.count()
        entries = list(queryset[:limit])
        filename = "payout_admin_ledger_export.csv"

        rows = [
            [
                str(entry.id),
                str(entry.wallet.trainer.user_id),
                getattr(entry.wallet.trainer, "display_name", ""),
                entry.entry_type,
                entry.direction,
                entry.status,
                _money(entry.amount),
                entry.currency,
                entry.source_type,
                str(entry.source_id),
                entry.created_at.isoformat(),
                entry.updated_at.isoformat(),
            ]
            for entry in entries
        ]

        filters = {
            key: _query_value(request.query_params, key)
            for key in ["status", "trainer_id", "currency", "entry_type", "direction", "source_type", "created_from", "created_to"]
        }
        _audit_context(
            request=request,
            export_type="ledger",
            filename=filename,
            filters=filters,
            exported_rows=len(rows),
            total_rows=total_rows,
            limit=limit,
        )

        return _csv_response(
            filename=filename,
            header=[
                "id",
                "trainer_id",
                "trainer_name",
                "entry_type",
                "direction",
                "status",
                "amount",
                "currency",
                "source_type",
                "source_id",
                "created_at",
                "updated_at",
            ],
            rows=rows,
        )
