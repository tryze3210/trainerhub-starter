from __future__ import annotations

from dataclasses import asdict

from apps.workflows.models import WorkflowRun

WORKFLOW_RUNS: list[WorkflowRun] = [
    WorkflowRun(
        id='wf_1',
        workflow_key='payment_finalize',
        subject_type='payment',
        subject_id='pay_1',
        status='running',
        current_step='grant_entitlements',
        tenant_id='tenant_studio_1',
        context={'order_id': 'ord_1', 'subscription_id': 'sub_11'},
    ),
    WorkflowRun(
        id='wf_2',
        workflow_key='content_publish_projection',
        subject_type='video',
        subject_id='vid_101',
        status='completed',
        current_step='done',
        tenant_id='tenant_studio_1',
        context={'projection_target': 'public_catalog'},
    ),
]


def list_workflow_runs() -> list[dict]:
    return [asdict(item) for item in WORKFLOW_RUNS]
