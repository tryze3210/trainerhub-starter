from apps.audit.models import AuditEvent


class AuditService:
    @staticmethod
    def log(*, actor=None, event_type: str, entity_type: str, entity_id: str, context=None, request=None):
        return AuditEvent.objects.create(
            actor=actor,
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            context=context or {},
            ip_address=(request.META.get('REMOTE_ADDR') if request else None),
            user_agent=(request.META.get('HTTP_USER_AGENT', '') if request else ''),
        )
