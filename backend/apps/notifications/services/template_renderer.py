from dataclasses import dataclass
from django.template import Context, Template
from apps.notifications.models import NotificationTemplate


@dataclass(slots=True)
class RenderedNotification:
    subject: str
    body: str
    template_code: str


class NotificationTemplateRenderer:
    def render(self, *, code: str, context: dict) -> RenderedNotification:
        template = NotificationTemplate.objects.get(code=code, is_active=True)
        ctx = Context(context)
        subject = Template(template.subject_template or "").render(ctx).strip()
        body = Template(template.body_template).render(ctx).strip()
        return RenderedNotification(subject=subject, body=body, template_code=template.code)
