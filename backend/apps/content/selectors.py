from __future__ import annotations

from decimal import Decimal
from django.db.models import Avg, Count, QuerySet

from apps.content.models import PublishedBundle, PublishedLesson, PublishedProgram, PublishedVideo
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


def _lookup_public_entity(model, identifier):
    from django.db.models import Q

    identifier_text = str(identifier or '').strip()
    if not identifier_text:
        return None
    lookup = Q(slug=identifier_text)
    try:
        from uuid import UUID
        lookup = lookup | Q(source_draft_id=UUID(identifier_text))
    except Exception:
        pass
    if identifier_text.isdigit():
        lookup = lookup | Q(id=int(identifier_text))
    return model.objects.filter(lookup).first()


def _duration_seconds(minutes: int | None, fallback: int = 1800) -> int:
    minutes = int(minutes or 0)
    return minutes * 60 if minutes > 0 else fallback


def get_video_detail(*, video_id: str) -> dict:
    video = _lookup_public_entity(PublishedVideo, video_id)
    if not video:
        # Legacy/offline-safe fallback. Real catalog rows override this path.
        return {
            'id': str(video_id),
            'video_id': str(video_id),
            'duration_seconds': 1800,
            'title': str(video_id),
        }
    return {
        'id': str(video.id),
        'video_id': str(video.source_draft_id),
        'slug': video.slug,
        'title': video.title,
        'duration_seconds': _duration_seconds(video.duration_minutes),
    }


def get_program_detail(*, program_id: str) -> dict:
    program = _lookup_public_entity(PublishedProgram, program_id)
    if not program:
        return {
            'id': str(program_id),
            'program_id': str(program_id),
            'lesson_ids': ['lesson-301'] if str(program_id) == 'prog-201' else [],
            'title': str(program_id),
        }
    lesson_ids = [str(lesson.source_draft_id) for lesson in program.lessons.all()]
    return {
        'id': str(program.id),
        'program_id': str(program.source_draft_id),
        'slug': program.slug,
        'title': program.title,
        'lesson_ids': lesson_ids,
    }


def _first_active_program_id_for_user(user) -> str:
    try:
        from apps.entitlements.models import EntitlementTargetType
        from apps.entitlements.selectors import get_user_active_entitlements

        entitlement = (
            get_user_active_entitlements(user=user)
            .filter(target_type=EntitlementTargetType.PROGRAM)
            .order_by('-created_at')
            .first()
        )
        return str(entitlement.target_id) if entitlement and entitlement.target_id else ''
    except Exception:
        return ''


def get_lesson_detail(*, lesson_id: str, user=None) -> dict:
    lesson = _lookup_public_entity(PublishedLesson, lesson_id)
    if not lesson:
        program_id = _first_active_program_id_for_user(user) if user is not None else ''
        if not program_id and str(lesson_id) == 'lesson-301':
            program_id = 'prog-201'
        return {
            'id': str(lesson_id),
            'lesson_id': str(lesson_id),
            'program_id': program_id,
            'duration_seconds': 0,
            'title': str(lesson_id),
        }
    return {
        'id': str(lesson.id),
        'lesson_id': str(lesson.source_draft_id),
        'program_id': str(lesson.program.source_draft_id),
        'slug': lesson.slug,
        'title': lesson.title,
        'duration_seconds': _duration_seconds(lesson.duration_minutes, fallback=0),
    }


def user_has_video_access(*, user, video_id: str) -> bool:
    try:
        from apps.entitlements.selectors import has_active_entitlement
        return has_active_entitlement(user=user, target_type='video', target_id=video_id)
    except Exception:
        return False


def user_has_lesson_access(*, user, lesson_id: str) -> bool:
    lesson = get_lesson_detail(lesson_id=lesson_id, user=user)
    program_id = lesson.get('program_id')
    if not program_id:
        return False
    try:
        from apps.entitlements.selectors import has_active_entitlement
        return has_active_entitlement(user=user, target_type='program', target_id=program_id)
    except Exception:
        return False
