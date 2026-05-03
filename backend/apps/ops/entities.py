from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Model
from django.forms.models import model_to_dict


@dataclass(frozen=True)
class AdminEntityDetail:
    entity_type: str
    entity_id: str
    title: str
    status: str
    primary: dict[str, Any]
    payload: dict[str, Any]
    relationships: list[dict[str, str]]
    raw: dict[str, Any]


class AdminEntityNotFound(ObjectDoesNotExist):
    pass


class UnsupportedAdminEntity(ValueError):
    pass


def _stringify(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, Model):
        return {
            'model': value._meta.label_lower,
            'id': str(value.pk),
        }
    if isinstance(value, dict):
        return {str(key): _stringify(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_stringify(item) for item in value]
    return value


def _model_dict(instance: Model) -> dict[str, Any]:
    data = model_to_dict(instance)
    for field in instance._meta.fields:
        name = field.name
        attname = getattr(field, 'attname', name)
        if getattr(field, 'is_relation', False):
            # Store FK objects as compact references and always expose *_id for filters/links.
            try:
                related = getattr(instance, name)
                data[name] = None if related is None else {
                    'model': related._meta.label_lower,
                    'id': str(related.pk),
                }
            except Exception:
                pass
        else:
            try:
                data[name] = getattr(instance, name)
            except Exception:
                pass
        if attname != name:
            try:
                data[attname] = getattr(instance, attname)
            except Exception:
                pass
    # Include common timestamp/status-like fields even if model_to_dict omits them.
    for attr in [
        'id',
        'pk',
        'status',
        'event_type',
        'aggregate_type',
        'aggregate_id',
        'topic',
        'consumer',
        'message_key',
        'provider',
        'external_event_id',
        'external_payment_id',
        'source_type',
        'source_id',
        'entry_type',
        'direction',
        'queue',
        'target_type',
        'target_id',
        'event_type',
        'entity_type',
        'entity_id',
        'created_at',
        'updated_at',
        'received_at',
        'processed_at',
        'occurred_at',
        'confirmed_at',
        'opened_at',
        'resolved_at',
    ]:
        if hasattr(instance, attr):
            try:
                data[attr] = getattr(instance, attr)
            except Exception:
                pass
    return _stringify(data)


def _get_uuid_model(model: type[Model], entity_id: str) -> Model:
    try:
        return model.objects.get(pk=entity_id)
    except model.DoesNotExist as exc:  # type: ignore[attr-defined]
        raise AdminEntityNotFound(f'{model.__name__} was not found.') from exc


def _rel(entity_type: str, entity_id: Any, label: str) -> dict[str, str] | None:
    if entity_id in {None, ''}:
        return None
    return {
        'entity_type': entity_type,
        'entity_id': str(entity_id),
        'label': label,
        'href': f'/admin/entities/{entity_type}/{entity_id}',
    }


def _compact_primary(raw: dict[str, Any], keys: list[str]) -> dict[str, Any]:
    return {key: raw.get(key) for key in keys if raw.get(key) not in {None, ''}}


def _with_relationships(*items: dict[str, str] | None) -> list[dict[str, str]]:
    seen: set[tuple[str, str]] = set()
    result: list[dict[str, str]] = []
    for item in items:
        if not item:
            continue
        key = (item['entity_type'], item['entity_id'])
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def get_admin_entity_detail(*, entity_type: str, entity_id: str) -> AdminEntityDetail:
    normalized = entity_type.strip().lower().replace('-', '_')

    if normalized in {'domain_event', 'event'}:
        from apps.events.models import DomainEvent

        obj = _get_uuid_model(DomainEvent, entity_id)
        raw = _model_dict(obj)
        title = raw.get('event_type') or 'Domain event'
        return AdminEntityDetail(
            entity_type='domain_event',
            entity_id=str(obj.pk),
            title=str(title),
            status='recorded',
            primary=_compact_primary(raw, ['event_type', 'aggregate_type', 'aggregate_id', 'tenant_id', 'idempotency_key', 'occurred_at']),
            payload=raw.get('payload') or {},
            relationships=_with_relationships(_rel(str(raw.get('aggregate_type') or ''), raw.get('aggregate_id'), 'Aggregate')),
            raw=raw,
        )

    if normalized in {'outbox', 'outbox_message'}:
        from apps.events.models import OutboxMessage

        obj = _get_uuid_model(OutboxMessage, entity_id)
        raw = _model_dict(obj)
        return AdminEntityDetail(
            entity_type='outbox_message',
            entity_id=str(obj.pk),
            title=str(raw.get('event_type') or raw.get('topic') or 'Outbox message'),
            status=str(raw.get('status') or 'unknown'),
            primary=_compact_primary(raw, ['status', 'topic', 'event_type', 'aggregate_type', 'aggregate_id', 'attempts', 'max_attempts', 'last_error', 'next_retry_at', 'processed_at']),
            payload=raw.get('payload') or {},
            relationships=_with_relationships(
                _rel('domain_event', raw.get('event_id'), 'Domain event'),
                _rel(str(raw.get('aggregate_type') or ''), raw.get('aggregate_id'), 'Aggregate'),
            ),
            raw=raw,
        )

    if normalized in {'inbox', 'inbox_message'}:
        from apps.events.models import InboxMessage

        obj = _get_uuid_model(InboxMessage, entity_id)
        raw = _model_dict(obj)
        return AdminEntityDetail(
            entity_type='inbox_message',
            entity_id=str(obj.pk),
            title=str(raw.get('consumer') or 'Inbox message'),
            status=str(raw.get('status') or 'unknown'),
            primary=_compact_primary(raw, ['consumer', 'message_key', 'status', 'processed_at', 'last_error']),
            payload=raw.get('payload') or {},
            relationships=_with_relationships(_rel('domain_event', raw.get('message_key'), 'Domain event')),
            raw=raw,
        )

    if normalized == 'payment':
        from apps.payments.models import Payment

        obj = _get_uuid_model(Payment, entity_id)
        raw = _model_dict(obj)
        return AdminEntityDetail(
            entity_type='payment',
            entity_id=str(obj.pk),
            title=f"Payment {raw.get('status') or ''}".strip(),
            status=str(raw.get('status') or 'unknown'),
            primary=_compact_primary(raw, ['status', 'provider', 'amount', 'currency', 'external_payment_id', 'order_id', 'confirmed_at']),
            payload=raw.get('provider_payload') or {},
            relationships=_with_relationships(_rel('order', raw.get('order_id'), 'Order')),
            raw=raw,
        )

    if normalized in {'payment_webhook', 'payment_webhook_event', 'webhook'}:
        from apps.payments.models import PaymentWebhookEvent

        obj = _get_uuid_model(PaymentWebhookEvent, entity_id)
        raw = _model_dict(obj)
        return AdminEntityDetail(
            entity_type='payment_webhook',
            entity_id=str(obj.pk),
            title=str(raw.get('event_type') or 'Payment webhook'),
            status=str(raw.get('status') or 'unknown'),
            primary=_compact_primary(raw, ['provider', 'event_type', 'external_event_id', 'status', 'payment_id', 'attempts', 'error_message', 'received_at', 'processed_at']),
            payload=raw.get('payload') or {},
            relationships=_with_relationships(_rel('payment', raw.get('payment_id'), 'Payment')),
            raw=raw,
        )

    if normalized == 'order':
        from apps.orders.models import Order

        obj = _get_uuid_model(Order, entity_id)
        raw = _model_dict(obj)
        return AdminEntityDetail(
            entity_type='order',
            entity_id=str(obj.pk),
            title=f"Order {raw.get('status') or ''}".strip(),
            status=str(raw.get('status') or 'unknown'),
            primary=_compact_primary(raw, ['status', 'order_type', 'total_amount', 'amount', 'currency', 'user_id', 'created_at', 'updated_at']),
            payload=raw.get('metadata') or raw.get('snapshot') or {},
            relationships=_with_relationships(_rel('user', raw.get('user_id'), 'Customer')),
            raw=raw,
        )

    if normalized in {'payout_ledger', 'ledger_entry', 'balance_entry'}:
        from apps.payouts.models import BalanceEntry

        obj = _get_uuid_model(BalanceEntry, entity_id)
        raw = _model_dict(obj)
        source_type = str(raw.get('source_type') or '')
        source_id = raw.get('source_id')
        source_entity = 'payment' if source_type in {'payment', 'payment_refund', 'payment_chargeback', 'payment_dispute_hold', 'payment_dispute_release'} else source_type
        return AdminEntityDetail(
            entity_type='payout_ledger',
            entity_id=str(obj.pk),
            title=str(raw.get('entry_type') or 'Payout ledger entry'),
            status=str(raw.get('status') or 'unknown'),
            primary=_compact_primary(raw, ['entry_type', 'direction', 'amount', 'currency', 'status', 'source_type', 'source_id', 'wallet_id', 'trainer_id', 'created_at']),
            payload=raw.get('metadata') or {},
            relationships=_with_relationships(_rel(source_entity, source_id, 'Source'), _rel('trainer_wallet', raw.get('wallet_id'), 'Trainer wallet')),
            raw=raw,
        )

    if normalized in {'payout_request'}:
        from apps.payouts.models import PayoutRequest

        obj = _get_uuid_model(PayoutRequest, entity_id)
        raw = _model_dict(obj)
        return AdminEntityDetail(
            entity_type='payout_request',
            entity_id=str(obj.pk),
            title=f"Payout request {raw.get('status') or ''}".strip(),
            status=str(raw.get('status') or 'unknown'),
            primary=_compact_primary(raw, ['status', 'amount', 'currency', 'trainer_id', 'wallet_id', 'destination_masked', 'created_at', 'updated_at']),
            payload=raw.get('metadata') or raw.get('destination_json') or {},
            relationships=_with_relationships(_rel('trainer_wallet', raw.get('wallet_id'), 'Trainer wallet')),
            raw=raw,
        )

    if normalized in {'moderation_case', 'case'}:
        from apps.moderation.models import ModerationCase

        obj = _get_uuid_model(ModerationCase, entity_id)
        raw = _model_dict(obj)
        return AdminEntityDetail(
            entity_type='moderation_case',
            entity_id=str(obj.pk),
            title=str(raw.get('title') or 'Moderation case'),
            status=str(raw.get('status') or 'unknown'),
            primary=_compact_primary(raw, ['queue', 'status', 'priority', 'target_type', 'target_id', 'trainer_id', 'latest_decision', 'opened_at', 'resolved_at']),
            payload={'summary': raw.get('summary') or ''},
            relationships=_with_relationships(_rel(str(raw.get('target_type') or ''), raw.get('target_id'), 'Target')),
            raw=raw,
        )

    if normalized in {'audit', 'audit_event'}:
        from apps.audit.models import AuditEvent

        obj = _get_uuid_model(AuditEvent, entity_id)
        raw = _model_dict(obj)
        context = raw.get('context') or {}
        target_type = context.get('target_type') or raw.get('entity_type')
        target_id = context.get('target_id') or raw.get('entity_id')
        return AdminEntityDetail(
            entity_type='audit_event',
            entity_id=str(obj.pk),
            title=str(raw.get('event_type') or 'Audit event'),
            status=str(context.get('status') or 'recorded'),
            primary=_compact_primary(raw, ['event_type', 'entity_type', 'entity_id', 'actor_id', 'ip_address', 'created_at', 'updated_at']),
            payload=context,
            relationships=_with_relationships(_rel(str(target_type or ''), target_id, 'Audited target')),
            raw=raw,
        )


    if normalized in {'reconciliation_snapshot', 'reconciliation'}:
        from apps.ops.models import ReconciliationSnapshot

        obj = _get_uuid_model(ReconciliationSnapshot, entity_id)
        raw = _model_dict(obj)
        return AdminEntityDetail(
            entity_type='reconciliation_snapshot',
            entity_id=str(obj.pk),
            title=f"Reconciliation snapshot {raw.get('status') or ''}".strip(),
            status=str(raw.get('status') or 'unknown'),
            primary=_compact_primary(raw, ['status', 'source', 'total_issues', 'critical_count', 'warning_count', 'info_count', 'generated_at', 'created_by_id', 'correlation_id']),
            payload={
                'summary': raw.get('summary') or {},
                'section_statuses': raw.get('section_statuses') or {},
            },
            relationships=_with_relationships(_rel('user', raw.get('created_by_id'), 'Created by')),
            raw=raw,
        )

    raise UnsupportedAdminEntity(f'Unsupported admin entity type: {entity_type}')
