from apps.legal_compliance.models import LegalAcceptanceSnapshot, LegalDocumentTemplate


class LegalAcceptanceService:
    @classmethod
    def accept_document(cls, *, user, actor_type: str, document: LegalDocumentTemplate, ip_address=None, user_agent=''):
        return LegalAcceptanceSnapshot.objects.create(
            user=user,
            actor_type=actor_type,
            document=document,
            ip_address=ip_address,
            user_agent=user_agent or '',
            body_snapshot=document.body_markdown,
            title_snapshot=document.title,
            version_snapshot=document.version,
        )
