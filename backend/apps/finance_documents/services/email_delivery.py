from __future__ import annotations

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone


class FinanceDocumentEmailDeliveryService:
    def send_document_ready(self, *, document, recipient_email: str, download_url: str, delivery_model):
        delivery = delivery_model.objects.create(
            document_id=document.id,
            recipient=recipient_email,
            channel="email",
        )
        try:
            subject = f"Your {document.document_type} {document.document_number} is ready"
            text_body = render_to_string(
                "finance_documents/email/document_ready.txt",
                {"document": document, "download_url": download_url},
            )
            html_body = render_to_string(
                "finance_documents/email/document_ready.html",
                {"document": document, "download_url": download_url},
            )
            message = EmailMultiAlternatives(subject=subject, body=text_body, to=[recipient_email])
            message.attach_alternative(html_body, "text/html")
            result = message.send()
            delivery.status = "sent"
            delivery.provider_message_id = str(result)
            delivery.sent_at = timezone.now()
            delivery.attempts += 1
            delivery.save(update_fields=["status", "provider_message_id", "sent_at", "attempts"])
        except Exception as exc:
            delivery.status = "failed"
            delivery.last_error = str(exc)
            delivery.attempts += 1
            delivery.save(update_fields=["status", "last_error", "attempts"])
            raise
        return delivery
