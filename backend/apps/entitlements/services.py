from django.db import transaction
from django.utils import timezone
from apps.entitlements.models import Entitlement

class EntitlementService:
    @staticmethod
    @transaction.atomic
    def grant(*, user, kind: str, object_id: str, source: str, source_reference: str, starts_at=None, ends_at=None, metadata=None):
        starts_at = starts_at or timezone.now()
        entitlement, _ = Entitlement.objects.update_or_create(
            user=user,
            kind=kind,
            object_id=str(object_id),
            source=source,
            source_reference=source_reference,
            defaults={
                'is_active': True,
                'starts_at': starts_at,
                'ends_at': ends_at,
                'metadata': metadata or {},
            }
        )
        return entitlement

    @staticmethod
    @transaction.atomic
    def revoke_by_source(*, source: str, source_reference: str):
        return Entitlement.objects.filter(source=source, source_reference=source_reference, is_active=True).update(is_active=False)
