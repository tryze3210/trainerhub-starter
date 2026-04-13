from django.db import transaction
from apps.trainers.models import TrainerProfile


class CreateTrainerProfileService:
    @transaction.atomic
    def execute(self, *, user, slug: str, display_name: str, headline: str = "", bio: str = ""):
        profile, created = TrainerProfile.objects.get_or_create(
            user=user,
            defaults={
                "slug": slug,
                "display_name": display_name,
                "headline": headline,
                "bio": bio,
            },
        )
        if not created:
            raise ValueError("Trainer profile already exists")
        return profile
