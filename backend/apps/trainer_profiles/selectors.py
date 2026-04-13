from django.db.models import Count
from apps.content.models import PublishedBundle, PublishedProgram, PublishedVideo
from apps.reviews.models import Review
from apps.trainer_profiles.models import TrainerPublicProfile


def _trainer_rating(profile: TrainerPublicProfile) -> tuple[float, int]:
    target_ids = [str(x.id) for x in PublishedVideo.objects.filter(trainer_profile=profile).only('id')]
    target_ids += [str(x.id) for x in PublishedProgram.objects.filter(trainer_profile=profile).only('id')]
    target_ids += [str(x.id) for x in PublishedBundle.objects.filter(trainer_profile=profile).only('id')]
    qs = Review.objects.filter(target_id__in=target_ids, status=Review.STATUS_PUBLISHED)
    count = qs.count()
    avg = round(sum(x.rating for x in qs) / count, 2) if count else 0.0
    return avg, count


def _serialize(profile: TrainerPublicProfile) -> dict:
    products_count = (
        PublishedVideo.objects.filter(trainer_profile=profile, is_active=True).count()
        + PublishedProgram.objects.filter(trainer_profile=profile, is_active=True).count()
        + PublishedBundle.objects.filter(trainer_profile=profile, is_active=True).count()
    )
    rating, reviews_count = _trainer_rating(profile)
    featured_items = [x.slug for x in PublishedVideo.objects.filter(trainer_profile=profile, is_featured=True)[:4]]
    return {
        'id': str(profile.trainer_uuid),
        'slug': profile.slug,
        'display_name': profile.display_name,
        'headline': profile.headline,
        'bio': profile.bio,
        'avatar_url': profile.avatar_url or 'https://cdn.example.com/placeholder-trainer.jpg',
        'specialties': profile.specialties,
        'languages': profile.languages,
        'rating': rating,
        'reviews_count': reviews_count,
        'students_count': 0,
        'active_products_count': products_count,
        'featured_items': featured_items,
    }


def list_public_trainers() -> list[dict]:
    profiles = TrainerPublicProfile.objects.filter(is_public=True).order_by('display_name')
    items = [_serialize(profile) for profile in profiles]
    return sorted(items, key=lambda x: (x['rating'], x['reviews_count'], x['active_products_count']), reverse=True)


def get_public_trainer(slug: str) -> dict | None:
    try:
        return _serialize(TrainerPublicProfile.objects.get(slug=slug, is_public=True))
    except TrainerPublicProfile.DoesNotExist:
        return None
