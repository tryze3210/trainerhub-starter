from apps.events import services as event_services
from apps.workflows import services as workflow_services


def test_emit_event_contract():
    payload = event_services.emit_event(
        event_name='payment.paid',
        aggregate_type='payment',
        aggregate_id='pay_001',
        payload={'amount': '49.00'},
    )
    assert payload['event_name'] == 'payment.paid'


def test_workflow_definitions_contract():
    payload = workflow_services.list_workflow_definitions()
    assert isinstance(payload, list)
