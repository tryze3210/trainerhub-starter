from django.utils import timezone

from apps.moderation.domain.models import TrainerRiskFlag


class TrainerRiskService:
    def raise_flag(self, *, trainer, code: str, label: str, risk_level: str, source: str = "manual", details=None):
        flag, _ = TrainerRiskFlag.objects.update_or_create(
            trainer=trainer,
            code=code,
            defaults={
                "label": label,
                "risk_level": risk_level,
                "source": source,
                "details": details or {},
                "is_active": True,
                "resolved_at": None,
            },
        )
        return flag

    def resolve_flag(self, *, flag: TrainerRiskFlag):
        flag.is_active = False
        flag.resolved_at = timezone.now()
        flag.save(update_fields=["is_active", "resolved_at"])
        return flag
