from __future__ import annotations

from django.contrib.auth import get_user_model
from django.utils.text import slugify

from apps.content import selectors as catalog_selectors
from apps.trainer_profiles import selectors
from apps.trainer_profiles.models import TrainerPublicProfile


User = get_user_model()


def _fallback_display_name(user) -> str:
    account_profile = getattr(user, 'account_profile', None)
    for candidate in [
        getattr(account_profile, 'display_name', ''),
        getattr(account_profile, 'full_name', ''),
        user.get_full_name(),
        getattr(getattr(user, 'trainer_profile', None), 'display_name', ''),
        user.email.split('@', 1)[0] if getattr(user, 'email', '') else '',
    ]:
        value = (candidate or '').strip()
        if value:
            return value
    return f'trainer-{user.pk}'


def ensure_trainer_public_profile(*, user=None, trainer_id=None) -> TrainerPublicProfile:
    if user is None and trainer_id is None:
        raise ValueError('user or trainer_id required')
    if user is None:
        try:
            profile = TrainerPublicProfile.objects.get(trainer_uuid=trainer_id)
            return profile
        except TrainerPublicProfile.DoesNotExist:
            raise LookupError(f'trainer profile not found for trainer_id={trainer_id}')

    display_name = _fallback_display_name(user)
    legacy_profile = getattr(user, 'trainer_profile', None)
    profile, created = TrainerPublicProfile.objects.get_or_create(
        user=user,
        defaults={
            'display_name': display_name,
            'headline': getattr(legacy_profile, 'headline', ''),
            'bio': getattr(legacy_profile, 'bio', ''),
            'slug': slugify(getattr(legacy_profile, 'slug', '') or display_name) or f'trainer-{user.pk}',
            'languages': [getattr(getattr(user, 'account_profile', None), 'preferred_language', 'en')],
            'is_public': getattr(legacy_profile, 'is_public', True),
        },
    )

    changed = False
    if legacy_profile:
        if profile.display_name != legacy_profile.display_name and legacy_profile.display_name:
            profile.display_name = legacy_profile.display_name
            changed = True
        if not profile.headline and legacy_profile.headline:
            profile.headline = legacy_profile.headline
            changed = True
        if not profile.bio and legacy_profile.bio:
            profile.bio = legacy_profile.bio
            changed = True
        if not profile.slug and legacy_profile.slug:
            profile.slug = legacy_profile.slug
            changed = True
        if profile.is_public != legacy_profile.is_public:
            profile.is_public = legacy_profile.is_public
            changed = True
    elif created and not profile.slug:
        profile.slug = slugify(display_name) or f'trainer-{user.pk}'
        changed = True

    if changed:
        profile.save(update_fields=['display_name', 'headline', 'bio', 'slug', 'is_public', 'updated_at'])
    return profile


def build_public_trainer_profile(slug: str) -> dict:
    trainer = selectors.get_public_trainer(slug)
    if not trainer:
        raise LookupError(f'Trainer not found: {slug}')
    items = [item for item in catalog_selectors.list_catalog_items({'trainer_slug': slug})]
    return {**trainer, 'catalog_items': items}
