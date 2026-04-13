from __future__ import annotations

from django.contrib.auth import get_user_model
from django.utils.text import slugify

from apps.content import selectors as catalog_selectors
from apps.trainer_profiles import selectors
from apps.trainer_profiles.models import TrainerPublicProfile


User = get_user_model()


def ensure_trainer_public_profile(*, user=None, trainer_id=None) -> TrainerPublicProfile:
    if user is None and trainer_id is None:
        raise ValueError('user or trainer_id required')
    if user is None:
        try:
            profile = TrainerPublicProfile.objects.get(trainer_uuid=trainer_id)
            return profile
        except TrainerPublicProfile.DoesNotExist:
            raise LookupError(f'trainer profile not found for trainer_id={trainer_id}')
    profile, _ = TrainerPublicProfile.objects.get_or_create(
        user=user,
        defaults={
            'display_name': getattr(getattr(user, 'account_profile', None), 'display_name', '') or getattr(getattr(user, 'account_profile', None), 'full_name', '') or user.username or user.email.split('@')[0],
            'headline': '',
            'bio': '',
            'slug': slugify((getattr(getattr(user, 'account_profile', None), 'display_name', '') or user.username or user.email.split('@')[0])) or f'trainer-{user.pk}',
            'languages': [getattr(getattr(user, 'account_profile', None), 'preferred_language', 'en')],
        },
    )
    return profile


def build_public_trainer_profile(slug: str) -> dict:
    trainer = selectors.get_public_trainer(slug)
    if not trainer:
        raise LookupError(f'Trainer not found: {slug}')
    items = [item for item in catalog_selectors.list_catalog_items({'trainer_slug': slug})]
    return {**trainer, 'catalog_items': items}
