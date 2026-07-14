from celery import shared_task
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.disputes.models import ChargebackOperation, DisputeCase, DisputeEvent, SupportInboxItem


@shared_task(name="disputes.sync_open_chargebacks")
def sync_open_chargebacks():
    now = timezone.now()
    marked_needs_evidence = 0

    with transaction.atomic():
        operations = (
            ChargebackOperation.objects.select_for_update()
            .select_related("dispute_case")
            .filter(status=ChargebackOperation.STATUS_OPEN, evidence_due_at__lte=now)
        )
        for operation in operations:
            evidence_payload = operation.evidence_payload or {}
            if evidence_payload.get("submitted_at"):
                continue
            operation.status = ChargebackOperation.STATUS_NEEDS_EVIDENCE
            provider_payload = dict(operation.provider_payload or {})
            provider_payload["needs_evidence_marked_at"] = now.isoformat()
            operation.provider_payload = provider_payload
            operation.save(update_fields=["status", "provider_payload", "updated_at"])
            DisputeEvent.objects.create(
                dispute_case=operation.dispute_case,
                event_type=DisputeEvent.EVENT_CHARGEBACK_SYNCED,
                body="Evidence due date passed without submission.",
                payload={
                    "action": "evidence_due",
                    "operation_id": str(operation.id),
                    "evidence_due_at": operation.evidence_due_at.isoformat() if operation.evidence_due_at else None,
                },
            )
            marked_needs_evidence += 1

    return {"status": "ok", "marked_needs_evidence": marked_needs_evidence}


@shared_task(name="disputes.sla_escalation_sweep")
def sla_escalation_sweep():
    hours = int(getattr(settings, "DISPUTE_SLA_ESCALATION_HOURS", 72))
    boundary = timezone.now() - timezone.timedelta(hours=hours)
    escalated = 0

    with transaction.atomic():
        cases = (
            DisputeCase.objects.select_for_update()
            .exclude(status__in=[DisputeCase.STATUS_RESOLVED, DisputeCase.STATUS_REJECTED, DisputeCase.STATUS_ESCALATED])
            .filter(opened_at__lte=boundary)
        )
        for case in cases:
            case.status = DisputeCase.STATUS_ESCALATED
            case.save(update_fields=["status", "updated_at"])
            SupportInboxItem.objects.filter(dispute_case=case).update(
                priority=SupportInboxItem.PRIORITY_HIGH,
                unread_for_admin=True,
            )
            DisputeEvent.objects.create(
                dispute_case=case,
                event_type=DisputeEvent.EVENT_STATUS_CHANGED,
                body=f"Dispute exceeded {hours}h SLA and was escalated.",
                payload={"status": DisputeCase.STATUS_ESCALATED, "sla_hours": hours},
            )
            escalated += 1

    return {"status": "ok", "sla_hours": hours, "escalated": escalated}
