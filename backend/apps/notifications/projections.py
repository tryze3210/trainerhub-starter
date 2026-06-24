from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable
from uuid import UUID

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Count
from django.utils import timezone

from apps.events.models import InboxMessage
from apps.notifications.models import DeliveryStatus, Notification, NotificationChannel, NotificationType


NOTIFICATION_PROJECTION_CONSUMER = 'notifications.event_projection'


@dataclass(frozen=True, slots=True)
class NotificationProjectionTemplate:
    notification_type: str
    title: str
    body: str
    recipient_keys: tuple[str, ...]
    cta_label: str = ''
    cta_url_key: str = ''


@dataclass(frozen=True, slots=True)
class NotificationProjectionResult:
    status: str
    topic: str
    message_key: str
    created_notifications: int = 0
    recipient_user_ids: tuple[str, ...] = ()
    reason: str = ''

    def as_dict(self) -> dict[str, Any]:
        return {
            'status': self.status,
            'topic': self.topic,
            'message_key': self.message_key,
            'created_notifications': self.created_notifications,
            'recipient_user_ids': list(self.recipient_user_ids),
            'reason': self.reason,
        }


class NotificationEventProjectionService:
    """Project domain events into durable in-app notifications.

    This projection is intentionally decoupled from payment/order/subscription
    services. Domain services emit facts; the outbox dispatcher calls this
    projection and creates user-facing notifications idempotently through the
    InboxMessage consumer key.
    """

    TOPIC_TEMPLATES: dict[str, NotificationProjectionTemplate] = {
        'payment.succeeded': NotificationProjectionTemplate(
            notification_type=NotificationType.PAYMENT,
            title='Оплата прошла',
            body='Платеж успешно обработан. Доступ к покупке будет открыт автоматически.',
            recipient_keys=('user_id', 'customer_id', 'buyer_id'),
            cta_label='Открыть покупки',
            cta_url_key='orders_url',
        ),
        'payment.paid': NotificationProjectionTemplate(
            notification_type=NotificationType.PAYMENT,
            title='Оплата прошла',
            body='Платеж успешно обработан. Доступ к покупке будет открыт автоматически.',
            recipient_keys=('user_id', 'customer_id', 'buyer_id'),
            cta_label='Открыть покупки',
            cta_url_key='orders_url',
        ),
        'payment.failed': NotificationProjectionTemplate(
            notification_type=NotificationType.PAYMENT,
            title='Платеж не прошел',
            body='Не удалось обработать платеж. Проверьте способ оплаты и попробуйте еще раз.',
            recipient_keys=('user_id', 'customer_id', 'buyer_id'),
            cta_label='Повторить оплату',
            cta_url_key='checkout_url',
        ),
        'payment.refunded': NotificationProjectionTemplate(
            notification_type=NotificationType.PAYMENT,
            title='Возврат оформлен',
            body='Возврат по платежу обработан. Доступ по заказу может быть отозван согласно правилам возврата.',
            recipient_keys=('user_id', 'customer_id', 'buyer_id'),
            cta_label='Открыть платежи',
            cta_url_key='billing_url',
        ),
        'payment.refund_partial': NotificationProjectionTemplate(
            notification_type=NotificationType.PAYMENT,
            title='Частичный возврат оформлен',
            body='Частичный возврат по платежу обработан. Доступ остается активным, если заказ не возвращен полностью.',
            recipient_keys=('user_id', 'customer_id', 'buyer_id'),
            cta_label='Открыть платежи',
            cta_url_key='billing_url',
        ),
        'payment.cancelled': NotificationProjectionTemplate(
            notification_type=NotificationType.PAYMENT,
            title='Платеж отменен',
            body='Платеж был отменен. Доступ по этому заказу не был открыт.',
            recipient_keys=('user_id', 'customer_id', 'buyer_id'),
            cta_label='К заказам',
            cta_url_key='orders_url',
        ),
        'payment.dispute_opened': NotificationProjectionTemplate(
            notification_type=NotificationType.PAYMENT,
            title='Платеж оспаривается',
            body='Платеж по заказу перешел в спор. Доступ пока не отозван, но заказ требует проверки поддержки.',
            recipient_keys=('user_id', 'customer_id', 'buyer_id'),
            cta_label='Открыть платеж',
            cta_url_key='payment_url',
        ),
        'payment.chargeback_lost': NotificationProjectionTemplate(
            notification_type=NotificationType.PAYMENT,
            title='Платеж оспорен',
            body='Платеж был принудительно возвращен платежной системой. Доступ по заказу отозван.',
            recipient_keys=('user_id', 'customer_id', 'buyer_id'),
            cta_label='Открыть платеж',
            cta_url_key='payment_url',
        ),
        'payment.charged_back': NotificationProjectionTemplate(
            notification_type=NotificationType.PAYMENT,
            title='Платеж оспорен',
            body='Платеж был принудительно возвращен платежной системой. Доступ по заказу отозван.',
            recipient_keys=('user_id', 'customer_id', 'buyer_id'),
            cta_label='Открыть платеж',
            cta_url_key='payment_url',
        ),
        'payment.chargeback_won': NotificationProjectionTemplate(
            notification_type=NotificationType.PAYMENT,
            title='Спор по платежу закрыт',
            body='Спор по платежу закрыт в пользу платформы. Оплата снова считается подтвержденной.',
            recipient_keys=('user_id', 'customer_id', 'buyer_id'),
            cta_label='Открыть платеж',
            cta_url_key='payment_url',
        ),
        'order.disputed': NotificationProjectionTemplate(
            notification_type=NotificationType.ORDER,
            title='Заказ в споре',
            body='По заказу открыт платежный спор. Поддержка проверит ситуацию.',
            recipient_keys=('user_id', 'customer_id', 'buyer_id'),
            cta_label='К заказу',
            cta_url_key='orders_url',
        ),
        'order.chargeback_lost': NotificationProjectionTemplate(
            notification_type=NotificationType.ORDER,
            title='Заказ отозван из-за chargeback',
            body='Платеж по заказу был оспорен и возвращен платежной системой. Доступы отозваны.',
            recipient_keys=('user_id', 'customer_id', 'buyer_id'),
            cta_label='К заказу',
            cta_url_key='orders_url',
        ),
        'order.dispute_won': NotificationProjectionTemplate(
            notification_type=NotificationType.ORDER,
            title='Спор по заказу закрыт',
            body='Спор по платежу закрыт в пользу платформы. Заказ снова считается оплаченным.',
            recipient_keys=('user_id', 'customer_id', 'buyer_id'),
            cta_label='К заказу',
            cta_url_key='orders_url',
        ),
        'order.paid': NotificationProjectionTemplate(
            notification_type=NotificationType.ORDER,
            title='Заказ оплачен',
            body='Заказ оплачен. Мы открываем доступ к купленному контенту.',
            recipient_keys=('user_id', 'customer_id', 'buyer_id'),
            cta_label='Открыть доступы',
            cta_url_key='access_url',
        ),
        'order.completed': NotificationProjectionTemplate(
            notification_type=NotificationType.ORDER,
            title='Заказ завершен',
            body='Заказ завершен, доступ к контенту активен.',
            recipient_keys=('user_id', 'customer_id', 'buyer_id'),
            cta_label='Открыть доступы',
            cta_url_key='access_url',
        ),
        'entitlement.granted': NotificationProjectionTemplate(
            notification_type=NotificationType.SYSTEM,
            title='Доступ открыт',
            body='Новый доступ к контенту активирован в вашем аккаунте.',
            recipient_keys=('user_id', 'customer_id', 'buyer_id'),
            cta_label='Открыть доступы',
            cta_url_key='access_url',
        ),
        'entitlement.revoked': NotificationProjectionTemplate(
            notification_type=NotificationType.SYSTEM,
            title='Доступ отозван',
            body='Один из доступов был отозван. Подробности доступны в личном кабинете.',
            recipient_keys=('user_id', 'customer_id', 'buyer_id'),
            cta_label='Открыть доступы',
            cta_url_key='access_url',
        ),
        'entitlement.expired': NotificationProjectionTemplate(
            notification_type=NotificationType.SYSTEM,
            title='Доступ истек',
            body='Срок действия одного из доступов завершился.',
            recipient_keys=('user_id', 'customer_id', 'buyer_id'),
            cta_label='Открыть доступы',
            cta_url_key='access_url',
        ),
        'subscription.activated': NotificationProjectionTemplate(
            notification_type=NotificationType.SUBSCRIPTION,
            title='Подписка активирована',
            body='Подписка активирована. Доступ к библиотеке открыт на оплаченный период.',
            recipient_keys=('user_id', 'customer_id', 'buyer_id'),
            cta_label='Открыть подписки',
            cta_url_key='subscriptions_url',
        ),
        'subscription.reactivated': NotificationProjectionTemplate(
            notification_type=NotificationType.SUBSCRIPTION,
            title='Подписка возобновлена',
            body='Подписка снова активна. Доступ к библиотеке восстановлен.',
            recipient_keys=('user_id', 'customer_id', 'buyer_id'),
            cta_label='Открыть подписки',
            cta_url_key='subscriptions_url',
        ),
        'subscription.cancelled': NotificationProjectionTemplate(
            notification_type=NotificationType.SUBSCRIPTION,
            title='Подписка отменена',
            body='Подписка отменена. Доступ сохранится до конца оплаченного периода, если он еще не истек.',
            recipient_keys=('user_id', 'customer_id', 'buyer_id'),
            cta_label='Открыть подписки',
            cta_url_key='subscriptions_url',
        ),
        'subscription.past_due': NotificationProjectionTemplate(
            notification_type=NotificationType.SUBSCRIPTION,
            title='Нужна оплата подписки',
            body='По подписке есть проблема с оплатой. Обновите способ оплаты, чтобы не потерять доступ.',
            recipient_keys=('user_id', 'customer_id', 'buyer_id'),
            cta_label='Обновить оплату',
            cta_url_key='billing_url',
        ),
        'subscription.expiring': NotificationProjectionTemplate(
            notification_type=NotificationType.SUBSCRIPTION,
            title='Подписка скоро закончится',
            body='Оплаченный период подписки скоро завершится. Проверьте продление в биллинге.',
            recipient_keys=('user_id', 'customer_id', 'buyer_id'),
            cta_label='Открыть подписки',
            cta_url_key='subscriptions_url',
        ),
        'payout.accrued': NotificationProjectionTemplate(
            notification_type=NotificationType.SYSTEM,
            title='Начислен доход',
            body='По продаже начислен доход. Он доступен в разделе выплат после прохождения правил вывода.',
            recipient_keys=('trainer_user_id', 'trainer_id', 'seller_id', 'user_id'),
            cta_label='Открыть выплаты',
            cta_url_key='payouts_url',
        ),
        'payout.requested': NotificationProjectionTemplate(
            notification_type=NotificationType.SYSTEM,
            title='Заявка на выплату создана',
            body='Заявка на выплату создана и ожидает обработки администратором.',
            recipient_keys=('trainer_user_id', 'trainer_id', 'seller_id', 'user_id'),
            cta_label='Открыть выплаты',
            cta_url_key='payouts_url',
        ),
        'payout.paid': NotificationProjectionTemplate(
            notification_type=NotificationType.SYSTEM,
            title='Выплата отправлена',
            body='Выплата отмечена как отправленная. Проверьте поступление по выбранному способу выплат.',
            recipient_keys=('trainer_user_id', 'trainer_id', 'seller_id', 'user_id'),
            cta_label='Открыть выплаты',
            cta_url_key='payouts_url',
        ),
        'payout.failed': NotificationProjectionTemplate(
            notification_type=NotificationType.SYSTEM,
            title='Выплата не прошла',
            body='Выплату не удалось обработать. Проверьте реквизиты или обратитесь в поддержку.',
            recipient_keys=('trainer_user_id', 'trainer_id', 'seller_id', 'user_id'),
            cta_label='Открыть выплаты',
            cta_url_key='payouts_url',
        ),
        'moderation.approved': NotificationProjectionTemplate(
            notification_type=NotificationType.SYSTEM,
            title='Материал прошел модерацию',
            body='Материал одобрен и может быть опубликован на платформе.',
            recipient_keys=('trainer_user_id', 'trainer_id', 'owner_id', 'user_id'),
        ),
        'moderation.rejected': NotificationProjectionTemplate(
            notification_type=NotificationType.SYSTEM,
            title='Материал не прошел модерацию',
            body='Материал отклонен модерацией. Исправьте замечания и отправьте его повторно.',
            recipient_keys=('trainer_user_id', 'trainer_id', 'owner_id', 'user_id'),
        ),
    }

    def project_outbox_payload(self, *, topic: str, payload: dict[str, Any] | None) -> dict[str, Any]:
        envelope = payload or {}
        message_key = self._message_key(envelope=envelope, topic=topic)
        template = self.TOPIC_TEMPLATES.get(topic)
        if not template:
            self._record_inbox(
                message_key=message_key,
                topic=topic,
                envelope=envelope,
                projection_status='skipped',
                reason='Topic is not mapped to notification projection.',
                notification_ids=[],
                recipient_user_ids=[],
            )
            return NotificationProjectionResult(
                status='skipped',
                topic=topic,
                message_key=message_key,
                reason='Topic is not mapped to notification projection.',
            ).as_dict()

        recipient_user_ids = self._recipient_user_ids(envelope=envelope, recipient_keys=template.recipient_keys)
        if not recipient_user_ids:
            self._record_inbox(
                message_key=message_key,
                topic=topic,
                envelope=envelope,
                projection_status='skipped',
                reason='No valid recipient user id was present in event payload.',
                notification_ids=[],
                recipient_user_ids=[],
            )
            return NotificationProjectionResult(
                status='skipped',
                topic=topic,
                message_key=message_key,
                reason='No valid recipient user id was present in event payload.',
            ).as_dict()

        with transaction.atomic():
            existing = InboxMessage.objects.select_for_update().filter(
                consumer=NOTIFICATION_PROJECTION_CONSUMER,
                message_key=message_key[:160],
                payload__projection_status='projected',
            ).first()
            if existing:
                notification_ids = existing.payload.get('notification_ids') or []
                return NotificationProjectionResult(
                    status='already_projected',
                    topic=topic,
                    message_key=message_key,
                    created_notifications=0,
                    recipient_user_ids=tuple(existing.payload.get('recipient_user_ids') or []),
                    reason=f'Already projected with {len(notification_ids)} notifications.',
                ).as_dict()

            valid_user_ids = self._existing_user_ids(recipient_user_ids)
            if not valid_user_ids:
                self._record_inbox(
                    message_key=message_key,
                    topic=topic,
                    envelope=envelope,
                    projection_status='skipped',
                    reason='Recipient user ids do not exist.',
                    notification_ids=[],
                    recipient_user_ids=recipient_user_ids,
                )
                return NotificationProjectionResult(
                    status='skipped',
                    topic=topic,
                    message_key=message_key,
                    recipient_user_ids=tuple(recipient_user_ids),
                    reason='Recipient user ids do not exist.',
                ).as_dict()

            notifications = Notification.objects.bulk_create(
                [
                    Notification(
                        user_id=user_id,
                        notification_type=template.notification_type,
                        channel=NotificationChannel.IN_APP,
                        title=template.title,
                        body=self._body(template=template, envelope=envelope),
                        cta_label=template.cta_label,
                        cta_url=self._cta_url(template=template, envelope=envelope),
                        metadata=self._metadata(topic=topic, envelope=envelope, message_key=message_key),
                        status=DeliveryStatus.SENT,
                        sent_at=timezone.now(),
                    )
                    for user_id in valid_user_ids
                ],
                batch_size=100,
            )
            notification_ids = [str(notification.notification_uuid) for notification in notifications]
            self._record_inbox(
                message_key=message_key,
                topic=topic,
                envelope=envelope,
                projection_status='projected',
                reason='',
                notification_ids=notification_ids,
                recipient_user_ids=valid_user_ids,
            )

        return NotificationProjectionResult(
            status='projected',
            topic=topic,
            message_key=message_key,
            created_notifications=len(notification_ids),
            recipient_user_ids=tuple(valid_user_ids),
        ).as_dict()

    def projection_health(self) -> dict[str, Any]:
        inbox_qs = InboxMessage.objects.filter(consumer=NOTIFICATION_PROJECTION_CONSUMER)
        latest = inbox_qs.order_by('-processed_at', '-created_at').first()
        notification_counts = (
            Notification.objects
            .filter(metadata__source='domain_event_outbox')
            .values('notification_type')
            .annotate(count=Count('id'))
            .order_by('notification_type')
        )
        return {
            'consumer': NOTIFICATION_PROJECTION_CONSUMER,
            'status': 'degraded' if inbox_qs.filter(status=InboxMessage.Status.FAILED).exists() else 'ok',
            'projected_messages': inbox_qs.filter(payload__projection_status='projected').count(),
            'skipped_messages': inbox_qs.filter(payload__projection_status='skipped').count(),
            'failed_messages': inbox_qs.filter(status=InboxMessage.Status.FAILED).count(),
            'created_notifications': Notification.objects.filter(metadata__source='domain_event_outbox').count(),
            'latest_processed_at': latest.processed_at if latest else None,
            'latest_message_key': latest.message_key if latest else '',
            'latest_payload': latest.payload if latest else {},
            'notification_counts': list(notification_counts),
        }

    def _record_inbox(
        self,
        *,
        message_key: str,
        topic: str,
        envelope: dict[str, Any],
        projection_status: str,
        reason: str,
        notification_ids: list[str],
        recipient_user_ids: Iterable[str],
    ) -> None:
        InboxMessage.objects.update_or_create(
            consumer=NOTIFICATION_PROJECTION_CONSUMER,
            message_key=message_key[:160],
            defaults={
                'status': InboxMessage.Status.PROCESSED,
                'payload': {
                    'topic': topic,
                    'projection_status': projection_status,
                    'reason': reason,
                    'notification_ids': list(notification_ids),
                    'recipient_user_ids': [str(value) for value in recipient_user_ids],
                    'event': envelope,
                },
                'processed_at': timezone.now(),
                'last_error': '',
            },
        )

    def _recipient_user_ids(self, *, envelope: dict[str, Any], recipient_keys: tuple[str, ...]) -> list[str]:
        domain_payload = envelope.get('payload') or {}
        domain_metadata = envelope.get('metadata') or {}
        values: list[str] = []
        for key in recipient_keys:
            for source in (domain_payload, domain_metadata, envelope):
                value = source.get(key)
                if value in (None, ''):
                    continue
                if isinstance(value, (list, tuple, set)):
                    values.extend(str(item) for item in value if item not in (None, ''))
                else:
                    values.append(str(value))
        # Keep order but remove duplicates.
        return list(dict.fromkeys(values))

    def _existing_user_ids(self, user_ids: list[str]) -> list[str]:
        valid_ids = []
        for user_id in user_ids:
            try:
                valid_ids.append(str(UUID(str(user_id))))
            except (TypeError, ValueError):
                continue
        if not valid_ids:
            return []
        User = get_user_model()
        existing = set(str(value) for value in User.objects.filter(id__in=valid_ids).values_list('id', flat=True))
        return [user_id for user_id in valid_ids if user_id in existing]

    def _body(self, *, template: NotificationProjectionTemplate, envelope: dict[str, Any]) -> str:
        domain_payload = envelope.get('payload') or {}
        amount = domain_payload.get('amount') or domain_payload.get('total_amount') or ''
        currency = domain_payload.get('currency') or ''
        suffix = ''
        if amount and currency:
            suffix = f' Сумма: {amount} {currency}.'
        return f'{template.body}{suffix}'

    def _cta_url(self, *, template: NotificationProjectionTemplate, envelope: dict[str, Any]) -> str:
        if not template.cta_url_key:
            return ''
        domain_payload = envelope.get('payload') or {}
        domain_metadata = envelope.get('metadata') or {}
        return str(domain_payload.get(template.cta_url_key) or domain_metadata.get(template.cta_url_key) or '')[:500]

    def _metadata(self, *, topic: str, envelope: dict[str, Any], message_key: str) -> dict[str, Any]:
        domain_payload = envelope.get('payload') or {}
        return {
            'source': 'domain_event_outbox',
            'topic': topic,
            'message_key': message_key,
            'domain_event_id': envelope.get('event_id'),
            'domain_event_type': envelope.get('event_type') or topic,
            'aggregate_type': envelope.get('aggregate_type'),
            'aggregate_id': envelope.get('aggregate_id'),
            'idempotency_key': envelope.get('idempotency_key'),
            'order_id': domain_payload.get('order_id') or '',
            'payment_id': domain_payload.get('payment_id') or '',
            'subscription_id': domain_payload.get('subscription_id') or '',
            'entitlement_id': domain_payload.get('entitlement_id') or '',
            'payout_id': domain_payload.get('payout_id') or '',
            'domain_payload': domain_payload,
            'domain_metadata': envelope.get('metadata') or {},
        }

    def _message_key(self, *, envelope: dict[str, Any], topic: str) -> str:
        return str(
            envelope.get('event_id')
            or envelope.get('idempotency_key')
            or f"{topic}:{envelope.get('aggregate_type', 'unknown')}:{envelope.get('aggregate_id', 'unknown')}"
        )[:160]


notification_projection_service = NotificationEventProjectionService()
