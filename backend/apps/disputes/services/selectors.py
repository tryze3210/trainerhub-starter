from django.db.models import Count, Q

from apps.disputes.models import DisputeCase


class DisputeSelectors:
    @staticmethod
    def admin_overview():
        qs = DisputeCase.objects.all()
        return {
            "total_cases": qs.count(),
            "open_cases": qs.exclude(status__in=[DisputeCase.STATUS_RESOLVED, DisputeCase.STATUS_REJECTED]).count(),
            "refund_cases": qs.filter(dispute_type=DisputeCase.TYPE_REFUND).count(),
            "chargeback_cases": qs.filter(dispute_type=DisputeCase.TYPE_CHARGEBACK).count(),
            "support_cases": qs.filter(dispute_type=DisputeCase.TYPE_SUPPORT).count(),
            "by_status": list(qs.values("status").annotate(total=Count("id")).order_by("status")),
        }

    @staticmethod
    def queue(filters: dict):
        qs = DisputeCase.objects.select_related("opened_by", "assigned_to")
        if filters.get("status"):
            qs = qs.filter(status=filters["status"])
        if filters.get("dispute_type"):
            qs = qs.filter(dispute_type=filters["dispute_type"])
        if filters.get("trainer_id"):
            qs = qs.filter(trainer_id=filters["trainer_id"])
        return qs.order_by("-created_at")
