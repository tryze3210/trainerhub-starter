from __future__ import annotations

import csv
from decimal import Decimal
from typing import Any, Callable, Iterable

from django.db.models import Count, Q
from django.http import HttpResponse
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework import generics, permissions, response, views

from apps.audit.services import AuditService
from apps.referrals.api.admin_serializers import (
    AdminReferralAttributionSerializer,
    AdminReferralInviteSerializer,
    AdminReferralLedgerSerializer,
    AdminReferralRewardSerializer,
)
from apps.referrals.models import ReferralAttribution, ReferralInvite, ReferralLedger, ReferralReward
from apps.referrals.selectors.admin_ops import AdminReferralOpsSelector
from common.csv_safe import csv_safe_value


MAX_CSV_EXPORT_ROWS = 10_000


def _param(request, name: str) -> str:
    return (request.query_params.get(name) or "").strip()


def _aware_datetime(raw_value: str):
    if not raw_value:
        return None
    parsed = parse_datetime(raw_value)
    if parsed is None:
        return None
    if timezone.is_naive(parsed):
        return timezone.make_aware(parsed, timezone.get_current_timezone())
    return parsed


def _apply_created_range(qs, request, *, field_name: str = "created_at"):
    created_from = _aware_datetime(_param(request, "created_from"))
    created_to = _aware_datetime(_param(request, "created_to"))
    if created_from:
        qs = qs.filter(**{f"{field_name}__gte": created_from})
    if created_to:
        qs = qs.filter(**{f"{field_name}__lte": created_to})
    return qs


def _csv_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, Decimal):
        return str(value.quantize(Decimal("0.01")))
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return csv_safe_value(value)


def _safe_getter(path: str) -> Callable[[Any], Any]:
    parts = path.split(".")

    def getter(obj: Any) -> Any:
        current = obj
        for part in parts:
            if current is None:
                return ""
            current = getattr(current, part, "")
        return current

    return getter



def _export_filters(request) -> dict[str, str]:
    allowed = (
        "status",
        "trigger_type",
        "trigger_reference",
        "entry_type",
        "owner_id",
        "referred_user_id",
        "reward_id",
        "program_slug",
        "code",
        "click_session_key",
        "utm_campaign",
        "search",
        "created_from",
        "created_to",
    )
    filters: dict[str, str] = {}
    for name in allowed:
        value = _param(request, name)
        if value:
            filters[name] = value
    return filters


def _audit_csv_export(
    request,
    *,
    export_kind: str,
    filename: str,
    row_count: int,
    total_count: int,
    limit: int = MAX_CSV_EXPORT_ROWS,
):
    AuditService.log_admin_action(
        actor=getattr(request, "user", None),
        request=request,
        action="referrals.csv_export",
        target_type="referral_export",
        target_id=export_kind,
        status="accepted",
        context={
            "export_kind": export_kind,
            "filename": filename,
            "row_count": row_count,
            "total_count": total_count,
            "limit": limit,
            "truncated": total_count > limit,
            "filters": _export_filters(request),
        },
    )

def _write_csv_response(*, filename: str, headers: list[str], rows: Iterable[dict[str, Any]]) -> HttpResponse:
    response_obj = HttpResponse(content_type="text/csv; charset=utf-8")
    response_obj["Content-Disposition"] = f'attachment; filename="{filename}"'
    response_obj.write("\ufeff")
    writer = csv.DictWriter(response_obj, fieldnames=headers, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow({key: _csv_value(row.get(key)) for key in headers})
    return response_obj


class AdminReferralOpsOverviewView(views.APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        try:
            days = int(request.query_params.get("days", 30))
        except (TypeError, ValueError):
            days = 30
        return response.Response(AdminReferralOpsSelector.overview(days=days))


class AdminReferralRewardListView(generics.ListAPIView):
    permission_classes = [permissions.IsAdminUser]
    serializer_class = AdminReferralRewardSerializer

    def get_queryset(self):
        qs = (
            ReferralReward.objects.select_related(
                "attribution__referred_user",
                "attribution__invite__code__owner",
                "attribution__invite__code__program",
            )
            .annotate(ledger_entry_count=Count("ledger_entries"))
            .order_by("-created_at")
        )
        qs = _apply_created_range(qs, self.request)

        if status := _param(self.request, "status"):
            qs = qs.filter(status=status)
        if trigger_type := _param(self.request, "trigger_type"):
            qs = qs.filter(trigger_type=trigger_type)
        if trigger_reference := _param(self.request, "trigger_reference"):
            qs = qs.filter(trigger_reference=trigger_reference)
        if owner_id := _param(self.request, "owner_id"):
            qs = qs.filter(attribution__invite__code__owner_id=owner_id)
        if referred_user_id := _param(self.request, "referred_user_id"):
            qs = qs.filter(attribution__referred_user_id=referred_user_id)
        if program_slug := _param(self.request, "program_slug"):
            qs = qs.filter(attribution__invite__code__program__slug=program_slug)
        if search := _param(self.request, "search"):
            qs = qs.filter(
                Q(trigger_reference__icontains=search)
                | Q(attribution__invite__code__code__icontains=search)
                | Q(attribution__invite__code__owner__email__icontains=search)
                | Q(attribution__referred_user__email__icontains=search)
            )
        return qs


class AdminReferralRewardDetailView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAdminUser]
    serializer_class = AdminReferralRewardSerializer

    def get_queryset(self):
        return ReferralReward.objects.select_related(
            "attribution__referred_user",
            "attribution__invite__code__owner",
            "attribution__invite__code__program",
        ).annotate(ledger_entry_count=Count("ledger_entries"))


class AdminReferralRewardExportView(AdminReferralRewardListView):
    pagination_class = None

    def get(self, request, *args, **kwargs):
        filename = "referral_rewards.csv"
        queryset = self.get_queryset()
        total_count = queryset.count()
        rows = []
        for reward in queryset[:MAX_CSV_EXPORT_ROWS]:
            rows.append(
                {
                    "id": reward.id,
                    "status": reward.status,
                    "amount": reward.amount,
                    "trigger_type": reward.trigger_type,
                    "trigger_reference": reward.trigger_reference,
                    "ledger_entry_count": getattr(reward, "ledger_entry_count", ""),
                    "program_slug": reward.attribution.invite.code.program.slug,
                    "code_value": reward.attribution.invite.code.code,
                    "owner_id": reward.attribution.invite.code.owner_id,
                    "owner_email": reward.attribution.invite.code.owner.email,
                    "referred_user_id": reward.attribution.referred_user_id,
                    "referred_user_email": reward.attribution.referred_user.email,
                    "created_at": reward.created_at,
                }
            )
        _audit_csv_export(
            request,
            export_kind="rewards",
            filename=filename,
            row_count=len(rows),
            total_count=total_count,
        )
        return _write_csv_response(
            filename=filename,
            headers=[
                "id",
                "status",
                "amount",
                "trigger_type",
                "trigger_reference",
                "ledger_entry_count",
                "program_slug",
                "code_value",
                "owner_id",
                "owner_email",
                "referred_user_id",
                "referred_user_email",
                "created_at",
            ],
            rows=rows,
        )


class AdminReferralLedgerListView(generics.ListAPIView):
    permission_classes = [permissions.IsAdminUser]
    serializer_class = AdminReferralLedgerSerializer

    def get_queryset(self):
        qs = (
            ReferralLedger.objects.select_related(
                "owner",
                "reward__attribution__referred_user",
                "reward__attribution__invite__code__program",
                "reward__attribution__invite__code__owner",
            )
            .order_by("-created_at")
        )
        qs = _apply_created_range(qs, self.request)

        if entry_type := _param(self.request, "entry_type"):
            qs = qs.filter(entry_type=entry_type)
        if owner_id := _param(self.request, "owner_id"):
            qs = qs.filter(owner_id=owner_id)
        if reward_id := _param(self.request, "reward_id"):
            qs = qs.filter(reward_id=reward_id)
        if program_slug := _param(self.request, "program_slug"):
            qs = qs.filter(reward__attribution__invite__code__program__slug=program_slug)
        if search := _param(self.request, "search"):
            qs = qs.filter(
                Q(owner__email__icontains=search)
                | Q(reward__trigger_reference__icontains=search)
                | Q(reward__attribution__referred_user__email__icontains=search)
            )
        return qs


class AdminReferralLedgerExportView(AdminReferralLedgerListView):
    pagination_class = None

    def get(self, request, *args, **kwargs):
        filename = "referral_ledger.csv"
        queryset = self.get_queryset()
        total_count = queryset.count()
        rows = []
        for entry in queryset[:MAX_CSV_EXPORT_ROWS]:
            reward = entry.reward
            attribution = reward.attribution if reward else None
            invite = attribution.invite if attribution else None
            code = invite.code if invite else None
            rows.append(
                {
                    "id": entry.id,
                    "entry_type": entry.entry_type,
                    "amount": entry.amount,
                    "balance_after": entry.balance_after,
                    "owner_id": entry.owner_id,
                    "owner_email": entry.owner.email,
                    "reward_id": entry.reward_id,
                    "reward_status": reward.status if reward else "",
                    "trigger_type": reward.trigger_type if reward else "",
                    "trigger_reference": reward.trigger_reference if reward else "",
                    "program_slug": code.program.slug if code else "",
                    "referred_user_id": attribution.referred_user_id if attribution else "",
                    "referred_user_email": attribution.referred_user.email if attribution else "",
                    "created_at": entry.created_at,
                }
            )
        _audit_csv_export(
            request,
            export_kind="ledger",
            filename=filename,
            row_count=len(rows),
            total_count=total_count,
        )
        return _write_csv_response(
            filename=filename,
            headers=[
                "id",
                "entry_type",
                "amount",
                "balance_after",
                "owner_id",
                "owner_email",
                "reward_id",
                "reward_status",
                "trigger_type",
                "trigger_reference",
                "program_slug",
                "referred_user_id",
                "referred_user_email",
                "created_at",
            ],
            rows=rows,
        )


class AdminReferralInviteListView(generics.ListAPIView):
    permission_classes = [permissions.IsAdminUser]
    serializer_class = AdminReferralInviteSerializer

    def get_queryset(self):
        qs = (
            ReferralInvite.objects.select_related(
                "code__owner",
                "code__program",
                "attribution__referred_user",
            )
            .order_by("-created_at")
        )
        qs = _apply_created_range(qs, self.request)

        if status := _param(self.request, "status"):
            qs = qs.filter(status=status)
        if code := _param(self.request, "code"):
            qs = qs.filter(code__code=code.upper())
        if owner_id := _param(self.request, "owner_id"):
            qs = qs.filter(code__owner_id=owner_id)
        if program_slug := _param(self.request, "program_slug"):
            qs = qs.filter(code__program__slug=program_slug)
        if click_session_key := _param(self.request, "click_session_key"):
            qs = qs.filter(click_session_key=click_session_key)
        if utm_campaign := _param(self.request, "utm_campaign"):
            qs = qs.filter(utm_campaign=utm_campaign)
        if search := _param(self.request, "search"):
            qs = qs.filter(
                Q(code__code__icontains=search)
                | Q(code__owner__email__icontains=search)
                | Q(attribution__referred_user__email__icontains=search)
                | Q(landing_path__icontains=search)
            )
        return qs


class AdminReferralInviteExportView(AdminReferralInviteListView):
    pagination_class = None

    def get(self, request, *args, **kwargs):
        filename = "referral_invites.csv"
        queryset = self.get_queryset()
        total_count = queryset.count()
        rows = []
        for invite in queryset[:MAX_CSV_EXPORT_ROWS]:
            attribution = getattr(invite, "attribution", None)
            rows.append(
                {
                    "id": invite.id,
                    "code_value": invite.code.code,
                    "program_slug": invite.code.program.slug,
                    "owner_id": invite.code.owner_id,
                    "owner_email": invite.code.owner.email,
                    "status": invite.status,
                    "landing_path": invite.landing_path,
                    "utm_source": invite.utm_source,
                    "utm_medium": invite.utm_medium,
                    "utm_campaign": invite.utm_campaign,
                    "click_session_key": invite.click_session_key,
                    "attribution_id": attribution.id if attribution else "",
                    "referred_user_id": attribution.referred_user_id if attribution else "",
                    "referred_user_email": attribution.referred_user.email if attribution else "",
                    "expires_at": invite.expires_at,
                    "converted_at": invite.converted_at,
                    "created_at": invite.created_at,
                }
            )
        _audit_csv_export(
            request,
            export_kind="invites",
            filename=filename,
            row_count=len(rows),
            total_count=total_count,
        )
        return _write_csv_response(
            filename=filename,
            headers=[
                "id",
                "code_value",
                "program_slug",
                "owner_id",
                "owner_email",
                "status",
                "landing_path",
                "utm_source",
                "utm_medium",
                "utm_campaign",
                "click_session_key",
                "attribution_id",
                "referred_user_id",
                "referred_user_email",
                "expires_at",
                "converted_at",
                "created_at",
            ],
            rows=rows,
        )


class AdminReferralInviteDetailView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAdminUser]
    serializer_class = AdminReferralInviteSerializer

    def get_queryset(self):
        return ReferralInvite.objects.select_related(
            "code__owner",
            "code__program",
            "attribution__referred_user",
        )


class AdminReferralAttributionListView(generics.ListAPIView):
    permission_classes = [permissions.IsAdminUser]
    serializer_class = AdminReferralAttributionSerializer

    def get_queryset(self):
        qs = (
            ReferralAttribution.objects.select_related(
                "referred_user",
                "invite__code__owner",
                "invite__code__program",
            )
            .order_by("-created_at")
        )
        qs = _apply_created_range(qs, self.request)

        if owner_id := _param(self.request, "owner_id"):
            qs = qs.filter(invite__code__owner_id=owner_id)
        if referred_user_id := _param(self.request, "referred_user_id"):
            qs = qs.filter(referred_user_id=referred_user_id)
        if program_slug := _param(self.request, "program_slug"):
            qs = qs.filter(invite__code__program__slug=program_slug)
        if search := _param(self.request, "search"):
            qs = qs.filter(
                Q(invite__code__code__icontains=search)
                | Q(invite__code__owner__email__icontains=search)
                | Q(referred_user__email__icontains=search)
            )
        return qs
