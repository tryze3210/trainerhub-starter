from dataclasses import dataclass
from django.core.mail import send_mail
from django.conf import settings


@dataclass(slots=True)
class EmailSendResult:
    provider: str
    provider_message_id: str


class DjangoEmailBackendAdapter:
    provider_name = "django_email"

    def send(self, *, to_email: str, subject: str, body: str) -> EmailSendResult:
        sent = send_mail(
            subject=subject,
            message=body,
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
            recipient_list=[to_email],
            fail_silently=False,
        )
        if sent != 1:
            raise RuntimeError("Email provider did not confirm delivery enqueue")
        return EmailSendResult(provider=self.provider_name, provider_message_id="")
