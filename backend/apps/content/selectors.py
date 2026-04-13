from __future__ import annotations

from decimal import Decimal
from django.db.models import Avg, Count, QuerySet

from apps.content.models import PublishedBundle, PublishedProgram, PublishedVideo
from apps.reviews.models import Review


PUBLIC_ENTITY_MODELS = {
    'video': PublishedVideo,
    'program': PublishedProgram,
    'bundle': PublishedBundle,
}


def _rating_stats(entity_type: str, ids: list[str]) -> dict[str, dict[str, float | int]]:
    if not ids:
        return {}
    rows = (
        Review.objects.filter(target_type=entity_type, target_id__in=ids, status=Review.STATUS_PUBLISHED)
        .values('target_id')
        .annotate(average_rating=Avg('rating'), reviews_count=Count('id'))
    )
    return {
        row['target_id']: {
            'average_rating': float(row['average_rating'] or 0),
            'reviews_count': int(row['reviews_count'] or 0),
        }
        for row in rows
    }


def list_public_videos() -> QuerySet[PublishedVideo]:
    return PublishedVideo.objects.select_related('trainer_profile').filter(is_active=True, visibility='public')


def list_public_programs() -> QuerySet[PublishedProgram]:
    return PublishedProgram.objects.select_related('trainer_profile').prefetch_related('lessons').filter(is_active=True, visibility='public')


def list_public_bundles() -> QuerySet[PublishedBundle]:
    return PublishedBundle.objects.select_related('trainer_profile').prefetch_related('items').filter(is_active=True, visibility='public')


def serialize_catalog_item(instance, entity_type: str) -> dict:
    stats = _rating_stats(entity_type, [str(instance.id)]).get(str(instance.id), {'average_rating': 0.0, 'reviews_count': 0})
    return {
        'id': str(instance.id),
        'entity_type': entity_type,
        'slug': instance.slug,
        'title': instance.title,
        'trainer_slug': instance.trainer_profile.slug,
        'trainer_name': instance.trainer_profile.display_name,
        'category': getattr(instance, 'category', 'fitness'),
        'difficulty': getattr(instance, 'difficulty', 'beginner'),
        'price': str(getattr(instance, 'price_amount', Decimal('0.00'))),
        'currency': getattr(instance, 'currency', 'EUR'),
        'rating': stats['average_rating'],
        'reviews_count': stats['reviews_count'],
        'duration_minutes': getattr(instance, 'duration_minutes', 0),
        'is_featured': bool(getattr(instance, 'is_featured', False)),
        'cover_url': instance.trainer_profile.avatar_url or 'https://cdn.example.com/placeholder-cover.jpg',
        'description': instance.description,
        'published_at': instance.published_at.isoformat(),
    }


def list_catalog_items(params: dict[str, str]) -> list[dict]:
    q = (params.get('q') or '').strip().lower()
    entity_type = params.get('entity_type')
    category = params.get('category')
    difficulty = params.get('difficulty')
    trainer_slug = params.get('trainer_slug')
    featured = params.get('featured')
    sort = params.get('sort') or 'newest'

    items: list[dict] = []
    entity_plan = [('video', list_public_videos()), ('program', list_public_programs()), ('bundle', list_public_bundles())]
    for kind, queryset in entity_plan:
        if entity_type and kind != entity_type:
            continue
        for obj in queryset:
            item = serialize_catalog_item(obj, kind)
            items.append(item)

    if q:
        items = [i for i in items if q in i['title'].lower() or q in i['description'].lower() or q in i['trainer_name'].lower()]
    if category:
        items = [i for i in items if i['category'] == category]
    if difficulty:
        items = [i for i in items if i['difficulty'] == difficulty]
    if trainer_slug:
        items = [i for i in items if i['trainer_slug'] == trainer_slug]
    if featured in {'1', 'true', 'True'}:
        items = [i for i in items if i['is_featured']]

    if sort == 'price_asc':
        items.sort(key=lambda x: float(x['price']))
    elif sort == 'price_desc':
        items.sort(key=lambda x: float(x['price']), reverse=True)
    elif sort == 'rating':
        items.sort(key=lambda x: (x['rating'], x['reviews_count']), reverse=True)
    elif sort == 'popular':
        items.sort(key=lambda x: x['reviews_count'], reverse=True)
    else:
        items.sort(key=lambda x: x['published_at'], reverse=True)
    return items


def list_featured_items(limit: int = 8) -> list[dict]:
    items = [item for item in list_catalog_items({}) if item['is_featured']]
    items.sort(key=lambda x: (x['rating'], x['reviews_count']), reverse=True)
    return items[:limit]


def get_catalog_item_by_slug(entity_type: str, slug: str) -> dict | None:
    model = PUBLIC_ENTITY_MODELS.get(entity_type)
    if not model:
        return None
    try:
        obj = model.objects.select_related('trainer_profile').get(slug=slug, is_active=True)
    except model.DoesNotExist:
        return None
    return serialize_catalog_item(obj, entity_type)
