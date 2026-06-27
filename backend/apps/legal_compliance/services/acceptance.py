from apps.legal_compliance.models import ConsentLog, LegalAcceptanceSnapshot, LegalDocumentTemplate


REQUIRED_CUSTOMER_DOCUMENT_TYPES = [
    LegalDocumentTemplate.DOC_TERMS,
    LegalDocumentTemplate.DOC_PRIVACY,
    LegalDocumentTemplate.DOC_REFUND_POLICY,
]


DOCUMENT_CONSENT_TYPE = {
    LegalDocumentTemplate.DOC_TERMS: ConsentLog.CONSENT_TERMS,
    LegalDocumentTemplate.DOC_PRIVACY: ConsentLog.CONSENT_PRIVACY,
    LegalDocumentTemplate.DOC_REFUND_POLICY: ConsentLog.CONSENT_REFUND_POLICY,
    LegalDocumentTemplate.DOC_TRAINER_AGREEMENT: ConsentLog.CONSENT_TRAINER_AGREEMENT,
}


class LegalAcceptanceService:
    @classmethod
    def accept_document(cls, *, user, actor_type: str, document: LegalDocumentTemplate, ip_address=None, user_agent='', source='api'):
        existing = LegalAcceptanceSnapshot.objects.filter(
            user=user,
            actor_type=actor_type,
            document=document,
            version_snapshot=document.version,
        ).order_by('-accepted_at').first()
        if existing:
            return existing
        acceptance = LegalAcceptanceSnapshot.objects.create(
            user=user,
            actor_type=actor_type,
            document=document,
            ip_address=ip_address,
            user_agent=user_agent or '',
            body_snapshot=document.body_markdown,
            title_snapshot=document.title,
            version_snapshot=document.version,
        )
        consent_type = DOCUMENT_CONSENT_TYPE.get(document.doc_type)
        if consent_type:
            ConsentLog.objects.create(
                user=user,
                consent_type=consent_type,
                granted=True,
                source=source,
                document=document,
                acceptance=acceptance,
                ip_address=ip_address,
                user_agent=user_agent or '',
                metadata={
                    'actor_type': actor_type,
                    'document_type': document.doc_type,
                    'document_version': document.version,
                },
            )
        return acceptance

    @classmethod
    def active_required_documents(cls, *, actor_type: str = LegalAcceptanceSnapshot.ACTOR_USER):
        required = REQUIRED_CUSTOMER_DOCUMENT_TYPES
        if actor_type == LegalAcceptanceSnapshot.ACTOR_TRAINER:
            required = [*required, LegalDocumentTemplate.DOC_TRAINER_AGREEMENT]
        documents = []
        for doc_type in required:
            document = (
                LegalDocumentTemplate.objects.filter(doc_type=doc_type, is_active=True)
                .order_by('-published_at', '-created_at')
                .first()
            )
            if document:
                documents.append(document)
        return documents

    @classmethod
    def compliance_status(cls, *, user, actor_type: str = LegalAcceptanceSnapshot.ACTOR_USER) -> dict:
        documents = cls.active_required_documents(actor_type=actor_type)
        accepted = {}
        missing = []
        for document in documents:
            acceptance = (
                LegalAcceptanceSnapshot.objects.filter(
                    user=user,
                    actor_type=actor_type,
                    document=document,
                    version_snapshot=document.version,
                )
                .order_by('-accepted_at')
                .first()
            )
            accepted[document.doc_type] = {
                'required_document_id': str(document.id),
                'version': document.version,
                'accepted': bool(acceptance),
                'accepted_at': acceptance.accepted_at.isoformat() if acceptance else None,
                'acceptance_id': str(acceptance.id) if acceptance else '',
            }
            if not acceptance:
                missing.append(document.doc_type)
        return {
            'actor_type': actor_type,
            'is_compliant': not missing,
            'missing': missing,
            'documents': accepted,
        }
