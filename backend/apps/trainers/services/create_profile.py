from django.db import transaction

from apps.accounts.models import AccountRoleAssignment
from apps.onboarding.services import complete_step
from apps.trainer_profiles.services import ensure_trainer_public_profile
from apps.trainers.models import TrainerProfile
from apps.users.models import User


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
                "status": 'active',
            },
        )
        if not created:
            raise ValueError("Trainer profile already exists")

        if user.role != User.Roles.TRAINER:
            user.role = User.Roles.TRAINER
            user.save(update_fields=['role', 'updated_at'])

        AccountRoleAssignment.objects.get_or_create(
            user=user,
            role=AccountRoleAssignment.ROLE_TRAINER,
            defaults={'is_active': True},
        )
        user.role_assignments.filter(role=AccountRoleAssignment.ROLE_USER, is_active=True).update(is_active=False)
        user.role_assignments.filter(role=AccountRoleAssignment.ROLE_TRAINER).update(is_active=True)

        public_profile = ensure_trainer_public_profile(user=user)
        changed = False
        if public_profile.display_name != display_name:
            public_profile.display_name = display_name
            changed = True
        if public_profile.slug != slug:
            public_profile.slug = slug
            changed = True
        if public_profile.headline != headline:
            public_profile.headline = headline
            changed = True
        if public_profile.bio != bio:
            public_profile.bio = bio
            changed = True
        public_profile.is_public = profile.is_public
        if changed:
            public_profile.save()

        complete_step(user=user, code='trainer_profile', payload={'trainer_profile_id': str(profile.id)})
        return profile
