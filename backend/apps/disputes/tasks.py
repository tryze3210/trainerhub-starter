from celery import shared_task


@shared_task(name="disputes.sync_open_chargebacks")
def sync_open_chargebacks():
    return {"status": "ok", "detail": "provider sync seam"}


@shared_task(name="disputes.sla_escalation_sweep")
def sla_escalation_sweep():
    return {"status": "ok", "detail": "escalation seam"}
