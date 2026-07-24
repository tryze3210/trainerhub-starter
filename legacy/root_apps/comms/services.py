from __future__ import annotations

from dataclasses import dataclass
from string import Template

from django.db import transaction
from django.utils import timezone

from .constants import DeliveryStatus, NotificationCategory, NotificationChannel
from .exceptions import PreferenceSuppressedError, ProviderDispatchError, TemplateRenderError
from .models import (
    CommunicationLedger,
    DeliveryAttempt,
    NotificationMessage,
    NotificationPreference,
)
from .providers import ConsoleEmailProvider, ConsolePushProvider, ConsoleSMSProvider
from .selectors import get_active_suppression_rules, get_active_template


@dataclass
class RenderedTemplate:
    subject: str
    title: str
    body: str


class TemplateRenderService:
    def render(self, *, template_obj, context: dict) -> RenderedTemplate:
        try:
            subject = Template(template_obj.subject_template or "").safe_substitute(context)
            title = Template(template_obj.title_template or "").safe_substitute(context)
            body = Template(template_obj.body_template).safe_substitute(context)
            return RenderedTemplate(subject=subject, title=title, body=body)
        except Exception as exc:
            raise TemplateRenderError(str(exc)) from exc


class PreferenceService:
    def is_enabled(self, *, user, category: str, channel: str) -> bool:
        if category in {NotificationCategory.SYSTEM, NotificationCategory.SECURITY, NotificationCategory.BILLING, NotificationCategory.PAYOUT}:
            return True
        preference = NotificationPreference.objects.filter(
            user=user,
            category=category,
            channel=channel,
        ).first()
        return True if preference is None else preference.is_enabled


class SuppressionService:
    def check(self, *, user, category: str, channel: str, payload: dict):
        for rule in get_active_suppression_rules(category=category, channel=channel):
            if rule.is_currently_active():
                raise PreferenceSuppressedError(rule.reason or rule.code)


class NotificationOrchestratorService:
    def __init__(self):
        self.template_render_service = TemplateRenderService()
        self.preference_service = PreferenceService()
        self.suppression_service = SuppressionService()

    @transaction.atomic
    def queue_from_template(
        self,
        *,
        user,
        template_key: str,
        channel: str,
        category: str,
        context: dict,
        payload: dict,
        event_key: str,
        idempotency_key: str,
        correlation_id: str = "",
        scheduled_for=None,
        metadata: dict | None = None,
    ) -> NotificationMessage:
        existing = NotificationMessage.objects.filter(idempotency_key=idempotency_key).first()
        if existing:
            return existing

        if not self.preference_service.is_enabled(user=user, category=category, channel=channel):
            raise PreferenceSuppressedError("disabled by user preference")

        self.suppression_service.check(user=user, category=category, channel=channel, payload=payload)

        template_obj = get_active_template(key=template_key, channel=channel, locale=context.get("locale", "en"))
        if not template_obj:
            raise TemplateRenderError(f"active template not found: {template_key}/{channel}")

        rendered = self.template_render_service.render(template_obj=template_obj, context=context)

        message = NotificationMessage.objects.create(
            user=user,
            category=category,
            channel=channel,
            template=template_obj,
            event_key=event_key,
            idempotency_key=idempotency_key,
            subject=rendered.subject,
            title=rendered.title,
            body=rendered.body,
            payload=payload,
            metadata=metadata or {},
            correlation_id=correlation_id,
            scheduled_for=scheduled_for,
            status=DeliveryStatus.PENDING,
        )
        CommunicationLedger.objects.create(
            user=user,
            event_key=event_key,
            channel=channel,
            category=category,
            message=message,
            outcome="queued",
            data={"idempotency_key": idempotency_key},
        )
        return message


class ProviderRegistry:
    def get(self, channel: str):
        if channel == NotificationChannel.EMAIL:
            return ConsoleEmailProvider()
        if channel == NotificationChannel.PUSH:
            return ConsolePushProvider()
        if channel == NotificationChannel.SMS:
            return ConsoleSMSProvider()
        return None


class MessageDispatchService:
    def __init__(self):
        self.provider_registry = ProviderRegistry()

    @transaction.atomic
    def dispatch(self, *, message: NotificationMessage) -> NotificationMessage:
        provider = self.provider_registry.get(message.channel)
        if provider is None:
            message.status = DeliveryStatus.SUPPRESSED
            message.suppressed_reason = "no provider for channel"
            message.save(update_fields=["status", "suppressed_reason", "updated_at"])
            CommunicationLedger.objects.create(
                user=message.user,
                event_key=message.event_key,
                channel=message.channel,
                category=message.category,
                message=message,
                outcome="suppressed",
                data={"reason": message.suppressed_reason},
            )
            return message

        message.status = DeliveryStatus.DISPATCHING
        message.save(update_fields=["status", "updated_at"])
        result = provider.send(message)
        DeliveryAttempt.objects.create(
            message=message,
            provider=provider.provider_code,
            status=DeliveryStatus.SENT if result.ok else DeliveryStatus.FAILED,
            request_payload={"subject": message.subject, "title": message.title},
            response_payload=result.response_payload or {},
            response_code=result.response_code,
            error_message=result.error_message,
        )
        if not result.ok:
            message.status = DeliveryStatus.FAILED
            message.save(update_fields=["status", "updated_at"])
            CommunicationLedger.objects.create(
                user=message.user,
                event_key=message.event_key,
                channel=message.channel,
                category=message.category,
                message=message,
                provider=provider.provider_code,
                outcome="failed",
                data={"error": result.error_message},
            )
            raise ProviderDispatchError(result.error_message or "provider dispatch failed")

        message.status = DeliveryStatus.SENT
        message.sent_at = timezone.now()
        message.save(update_fields=["status", "sent_at", "updated_at"])
        CommunicationLedger.objects.create(
            user=message.user,
            event_key=message.event_key,
            channel=message.channel,
            category=message.category,
            message=message,
            provider=provider.provider_code,
            outcome="sent",
            data={"response_code": result.response_code},
        )
        return message
