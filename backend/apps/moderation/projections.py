from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Count, Q
from django.utils import timezone

from apps.events.models import InboxMessage
from apps.moderation.models import (
    ModerationCase,
    ModerationCaseEvent,
    ModerationDecision,
    ModerationStatus,
    RiskLevel,
    TrainerRiskFlag,
)


MODERATION_RISK_PROJECTION_CONSUMER = 'moderation.risk_projection'
PAYMENT_RISK_QUEUE = 'payments_risk'
PAYMENT_TARGET_TYPE = 'payment'


@dataclass(frozen=True, slots=True)
class ModerationRiskProjectionResult:
    status: str
    topic: str
    message_key: str
    case_id: str = ''
    trainer_id: str = ''
    risk_flag_ids: tuple[str, ...] = ()
    reason: str = ''

    def as_dict(self) -> dict[str, Any]:
        return {
            'status': self.status,
            'topic': self.topic,
            'message_key': self.message_key,
            'case_id': self.case_id,
            'trainer_id': self.trainer_id,
            'risk_flag_ids': list(self.risk_flag_ids),
            'reason': self.reason,
        }


class ModerationRiskProjectionService:
    """Project payment risk events into moderation cases and trainer risk flags.

    Payment/refund services emit domain facts. This projection turns dispute and
    chargeback facts into operator work without coupling the payments module to
    the moderation module. Idempotency is persisted through InboxMessage.
    """

    SUPPORTED_TOPICS = {
        'payment.dispute_opened': {
            'title': 'Payment dispute opened',
            'event_type': 'payment_dispute_opened',
            'case_status': ModerationStatus.ESCALATED,
            'latest_decision': ModerationDecision.ESCALATED,
            'priority': 10,
            'risk_code': 'payment_dispute_opened',
            'risk_label': 'Payment dispute opened',
            'risk_level': RiskLevel.HIGH,
            'resolve_codes': (),
        },
        'payment.chargeback_lost': {
            'title': 'Payment chargeback lost',
            'event_type': 'payment_chargeback_lost',
            'case_status': ModerationStatus.ESCALATED,
            'latest_decision': ModerationDecision.ESCALATED,
            'priority': 5,
            'risk_code': 'payment_chargeback_lost',
            'risk_label': 'Payment chargeback lost',
            'risk_level': RiskLevel.CRITICAL,
            'resolve_codes': (),
        },
        'payment.chargeback_won': {
            'title': 'Payment chargeback won',
            'event_type': 'payment_chargeback_won',
            'case_status': ModerationStatus.RESOLVED,
            'latest_decision': ModerationDecision.APPROVED,
            'priority': 30,
            'risk_code': '',
            'risk_label': '',
            'risk_level': RiskLevel.LOW,
            'resolve_codes': ('payment_dispute_opened',),
        },
    }

    def project_outbox_payload(self, *, topic: str, payload: dict[str, Any] | None) -> dict[str, Any]:
        envelope = payload or {}
        message_key = self._message_key(envelope=envelope, topic=topic)
        spec = self.SUPPORTED_TOPICS.get(topic)
        if not spec:
            self._record_inbox(
                message_key=message_key,
                topic=topic,
                envelope=envelope,
                projection_status='skipped',
                reason='Topic is not mapped to moderation risk projection.',
            )
            return ModerationRiskProjectionResult(
                status='skipped',
                topic=topic,
                message_key=message_key,
                reason='Topic is not mapped to moderation risk projection.',
            ).as_dict()

        domain_payload = envelope.get('payload') or {}
        payment_id = str(domain_payload.get('payment_id') or envelope.get('aggregate_id') or '').strip()
        if not payment_id:
            self._record_inbox(
                message_key=message_key,
                topic=topic,
                envelope=envelope,
                projection_status='skipped',
                reason='No payment_id was present in event payload.',
            )
            return ModerationRiskProjectionResult(
                status='skipped',
                topic=topic,
                message_key=message_key,
                reason='No payment_id was present in event payload.',
            ).as_dict()

        with transaction.atomic():
            existing = InboxMessage.objects.select_for_update().filter(
                consumer=MODERATION_RISK_PROJECTION_CONSUMER,
                message_key=message_key[:160],
                payload__projection_status='projected',
            ).first()
            if existing:
                return ModerationRiskProjectionResult(
                    status='already_projected',
                    topic=topic,
                    message_key=message_key,
                    case_id=str(existing.payload.get('case_id') or ''),
                    trainer_id=str(existing.payload.get('trainer_id') or ''),
                    risk_flag_ids=tuple(existing.payload.get('risk_flag_ids') or []),
                    reason='Already projected.',
                ).as_dict()

            trainer = self._resolve_trainer(domain_payload=domain_payload)
            case = self._upsert_payment_case(
                topic=topic,
                payment_id=payment_id,
                trainer=trainer,
                domain_payload=domain_payload,
                spec=spec,
            )
            risk_flag_ids = self._apply_risk_flags(
                trainer=trainer,
                payment_id=payment_id,
                domain_payload=domain_payload,
                spec=spec,
            )
            self._record_inbox(
                message_key=message_key,
                topic=topic,
                envelope=envelope,
                projection_status='projected',
                reason='',
                case_id=str(case.id),
                trainer_id=str(trainer.id) if trainer else '',
                risk_flag_ids=risk_flag_ids,
            )

        return ModerationRiskProjectionResult(
            status='projected',
            topic=topic,
            message_key=message_key,
            case_id=str(case.id),
            trainer_id=str(trainer.id) if trainer else '',
            risk_flag_ids=tuple(risk_flag_ids),
        ).as_dict()

    def projection_health(self) -> dict[str, Any]:
        inbox_qs = InboxMessage.objects.filter(consumer=MODERATION_RISK_PROJECTION_CONSUMER)
        latest = inbox_qs.order_by('-processed_at', '-created_at').first()
        case_qs = ModerationCase.objects.filter(queue=PAYMENT_RISK_QUEUE)
        flag_qs = TrainerRiskFlag.objects.filter(source='payment_risk_projection')
        case_status_counts = list(
            case_qs.values('status')
            .annotate(count=Count('id'))
            .order_by('status')
        )
        flag_level_counts = list(
            flag_qs.filter(is_active=True)
            .values('risk_level')
            .annotate(count=Count('id'))
            .order_by('risk_level')
        )
        latest_cases = list(
            case_qs.order_by('-opened_at')
            .values('id', 'target_id', 'status', 'priority', 'title', 'opened_at')[:10]
        )
        return {
            'consumer': MODERATION_RISK_PROJECTION_CONSUMER,
            'status': 'degraded' if inbox_qs.filter(status=InboxMessage.Status.FAILED).exists() else 'ok',
            'projected_messages': inbox_qs.filter(payload__projection_status='projected').count(),
            'skipped_messages': inbox_qs.filter(payload__projection_status='skipped').count(),
            'failed_messages': inbox_qs.filter(status=InboxMessage.Status.FAILED).count(),
            'payment_risk_cases': case_qs.count(),
            'open_payment_risk_cases': case_qs.filter(status__in=[ModerationStatus.OPEN, ModerationStatus.IN_REVIEW, ModerationStatus.ESCALATED]).count(),
            'active_payment_risk_flags': flag_qs.filter(is_active=True).count(),
            'case_status_counts': case_status_counts,
            'flag_level_counts': flag_level_counts,
            'latest_processed_at': latest.processed_at if latest else None,
            'latest_message_key': latest.message_key if latest else '',
            'latest_payload': latest.payload if latest else {},
            'latest_cases': latest_cases,
        }

    def _upsert_payment_case(
        self,
        *,
        topic: str,
        payment_id: str,
        trainer,
        domain_payload: dict[str, Any],
        spec: dict[str, Any],
    ) -> ModerationCase:
        summary = self._case_summary(topic=topic, payment_id=payment_id, domain_payload=domain_payload)
        case, created = ModerationCase.objects.select_for_update().get_or_create(
            target_type=PAYMENT_TARGET_TYPE,
            target_id=payment_id[:64],
            queue=PAYMENT_RISK_QUEUE,
            defaults={
                'trainer': trainer,
                'status': spec['case_status'],
                'priority': spec['priority'],
                'title': spec['title'],
                'summary': summary,
                'latest_decision': spec['latest_decision'],
                'resolved_at': timezone.now() if spec['case_status'] == ModerationStatus.RESOLVED else None,
            },
        )
        update_fields: list[str] = []
        for field, value in {
            'trainer': trainer or case.trainer,
            'status': spec['case_status'],
            'priority': min(case.priority, spec['priority']) if not created else spec['priority'],
            'title': spec['title'],
            'summary': summary,
            'latest_decision': spec['latest_decision'],
            'resolved_at': timezone.now() if spec['case_status'] == ModerationStatus.RESOLVED else None,
        }.items():
            if getattr(case, field) != value:
                setattr(case, field, value)
                update_fields.append(field)
        if update_fields:
            update_fields.append('updated_at')
            case.save(update_fields=update_fields)

        ModerationCaseEvent.objects.create(
            case=case,
            actor=None,
            event_type=spec['event_type'],
            payload={
                'topic': topic,
                'payment_id': payment_id,
                'order_id': domain_payload.get('order_id') or '',
                'amount': domain_payload.get('amount') or '',
                'currency': domain_payload.get('currency') or '',
                'provider': domain_payload.get('provider') or '',
                'provider_payload': domain_payload.get('provider_payload') or {},
            },
        )
        return case

    def _apply_risk_flags(self, *, trainer, payment_id: str, domain_payload: dict[str, Any], spec: dict[str, Any]) -> list[str]:
        if not trainer:
            return []

        now = timezone.now()
        for code in spec.get('resolve_codes') or ():
            TrainerRiskFlag.objects.filter(
                trainer=trainer,
                code=code,
                source='payment_risk_projection',
                is_active=True,
            ).update(is_active=False, resolved_at=now)

        code = spec.get('risk_code') or ''
        if not code:
            return []

        existing = TrainerRiskFlag.objects.filter(
            trainer=trainer,
            code=code,
            source='payment_risk_projection',
            is_active=True,
        ).first()
        details = {
            'payment_id': payment_id,
            'order_id': domain_payload.get('order_id') or '',
            'amount': domain_payload.get('amount') or '',
            'currency': domain_payload.get('currency') or '',
            'provider': domain_payload.get('provider') or '',
        }
        if existing:
            existing.label = spec['risk_label']
            existing.risk_level = spec['risk_level']
            existing.details = {**(existing.details or {}), **details}
            existing.save(update_fields=['label', 'risk_level', 'details'])
            return [str(existing.id)]

        flag = TrainerRiskFlag.objects.create(
            trainer=trainer,
            code=code,
            label=spec['risk_label'],
            risk_level=spec['risk_level'],
            source='payment_risk_projection',
            details=details,
        )
        return [str(flag.id)]

    def _resolve_trainer(self, *, domain_payload: dict[str, Any]):
        provider_payload = domain_payload.get('provider_payload') or {}
        candidates = [
            domain_payload.get('trainer_user_id'),
            domain_payload.get('trainer_id'),
            domain_payload.get('seller_id'),
            provider_payload.get('trainer_user_id'),
            provider_payload.get('trainer_id'),
            provider_payload.get('seller_id'),
        ]
        valid_ids: list[str] = []
        for candidate in candidates:
            if candidate in (None, ''):
                continue
            try:
                valid_ids.append(str(UUID(str(candidate))))
            except (TypeError, ValueError):
                continue
        if not valid_ids:
            return None
        User = get_user_model()
        return User.objects.filter(id__in=valid_ids).first()

    def _record_inbox(
        self,
        *,
        message_key: str,
        topic: str,
        envelope: dict[str, Any],
        projection_status: str,
        reason: str,
        case_id: str = '',
        trainer_id: str = '',
        risk_flag_ids: list[str] | None = None,
    ) -> None:
        InboxMessage.objects.update_or_create(
            consumer=MODERATION_RISK_PROJECTION_CONSUMER,
            message_key=message_key[:160],
            defaults={
                'status': InboxMessage.Status.PROCESSED,
                'payload': {
                    'topic': topic,
                    'projection_status': projection_status,
                    'reason': reason,
                    'case_id': case_id,
                    'trainer_id': trainer_id,
                    'risk_flag_ids': risk_flag_ids or [],
                    'event': envelope,
                },
                'processed_at': timezone.now(),
                'last_error': '',
            },
        )

    def _case_summary(self, *, topic: str, payment_id: str, domain_payload: dict[str, Any]) -> str:
        amount = domain_payload.get('amount') or ''
        currency = domain_payload.get('currency') or ''
        order_id = domain_payload.get('order_id') or ''
        provider = domain_payload.get('provider') or ''
        return (
            f'Payment risk event {topic} for payment {payment_id}. '
            f'Order: {order_id or "unknown"}. Provider: {provider or "unknown"}. '
            f'Amount: {amount or "unknown"} {currency or ""}.'
        ).strip()

    def _message_key(self, *, envelope: dict[str, Any], topic: str) -> str:
        return str(
            envelope.get('event_id')
            or envelope.get('idempotency_key')
            or f"{topic}:{envelope.get('aggregate_type', 'unknown')}:{envelope.get('aggregate_id', 'unknown')}"
        )[:160]


moderation_risk_projection_service = ModerationRiskProjectionService()
