from __future__ import annotations

from uuid import uuid4

from apps.events.services import DomainEventService
from apps.workflows import selectors
from apps.workflows.models import WorkflowRun


WORKFLOW_DEFINITIONS = {
    'payment_finalize': {
        'trigger_event': 'payments.payment_paid',
        'steps': ['verify_payment', 'mark_order_paid', 'grant_entitlements', 'generate_receipt', 'notify_user'],
    },
    'content_publish_projection': {
        'trigger_event': 'moderation.content_approved',
        'steps': ['lock_version', 'project_public_catalog', 'refresh_trainer_profile', 'emit_catalog_published'],
    },
    'media_processing': {
        'trigger_event': 'media.asset_uploaded',
        'steps': ['probe_file', 'enqueue_transcoding', 'attach_stream_variants', 'emit_media_ready'],
    },
}


class WorkflowService:
    event_service = DomainEventService()

    def list_definitions(self) -> list[dict]:
        return [{'workflow_key': key, **value} for key, value in WORKFLOW_DEFINITIONS.items()]

    def list_runs(self) -> list[dict]:
        return selectors.list_workflow_runs()

    def start(self, workflow_key: str, subject_type: str, subject_id: str, tenant_id: str | None = None, context: dict | None = None) -> dict:
        definition = WORKFLOW_DEFINITIONS[workflow_key]
        run = WorkflowRun(
            id=f'wf_{uuid4().hex[:10]}',
            workflow_key=workflow_key,
            subject_type=subject_type,
            subject_id=subject_id,
            status='running',
            current_step=definition['steps'][0],
            tenant_id=tenant_id,
            context=context or {},
        )
        selectors.WORKFLOW_RUNS.insert(0, run)
        self.event_service.emit(
            event_type='workflows.run_started',
            aggregate_type='workflow_run',
            aggregate_id=run.id,
            tenant_id=tenant_id,
            payload={'workflow_key': workflow_key, 'subject_type': subject_type, 'subject_id': subject_id},
        )
        return {
            'workflow_run': {
                'id': run.id,
                'workflow_key': run.workflow_key,
                'subject_type': run.subject_type,
                'subject_id': run.subject_id,
                'status': run.status,
                'current_step': run.current_step,
                'tenant_id': run.tenant_id,
                'context': run.context,
            },
            'status': 'started',
        }


def list_workflow_definitions() -> list[dict]:
    return WorkflowService().list_definitions()


def list_workflow_runs() -> list[dict]:
    return WorkflowService().list_runs()


def start_workflow(
    *,
    workflow_key: str,
    subject_type: str,
    subject_id: str,
    tenant_id: str | None = None,
    context: dict | None = None,
) -> dict:
    return WorkflowService().start(
        workflow_key=workflow_key,
        subject_type=subject_type,
        subject_id=subject_id,
        tenant_id=tenant_id,
        context=context,
    )
