from __future__ import annotations

from datetime import timedelta
from decimal import Decimal
from typing import Any

from django.db.models import Avg, Count
from django.utils import timezone

from apps.reviews.models import Review


CONTENT_TARGET_TYPES = {'video', 'program', 'course', 'bundle'}


def normalize_target(target_type: str, target_id: Any) -> tuple[str, str]:
    normalized_type = (target_type or '').strip().lower()
    aliases = {
        'videos': 'video',
        'published_video': 'video',
        'publishedvideo': 'video',
        'programs': 'program',
        'published_program': 'program',
        'publishedprogram': 'program',
        'courses': 'course',
        'course_draft': 'course',
        'trainer_course_draft': 'course',
        'bundles': 'bundle',
        'published_bundle': 'bundle',
        'publishedbundle': 'bundle',
        'trainer_profile': 'trainer',
        'trainerprofile': 'trainer',
    }
    normalized_type = aliases.get(normalized_type, normalized_type)
    normalized_id = str(target_id or '').strip()
    if not normalized_type:
        raise ValueError('target_type is required')
    if not normalized_id:
        raise ValueError('target_id is required')
    return normalized_type, normalized_id


def _round_rating(value: Any) -> float:
    if value is None:
        return 0.0
    try:
        return float(Decimal(str(value)).quantize(Decimal('0.01')))
    except Exception:
        return 0.0


def get_rating_summary(target_type: str, target_id: Any) -> dict[str, Any]:
    normalized_type, normalized_id = normalize_target(target_type, target_id)
    aggregate = Review.objects.filter(
        target_type=normalized_type,
        target_id=normalized_id,
        status=Review.STATUS_PUBLISHED,
    ).aggregate(count=Count('id'), average=Avg('rating'))
    distribution = {str(value): 0 for value in range(1, 6)}
    for row in (
        Review.objects.filter(
            target_type=normalized_type,
            target_id=normalized_id,
            status=Review.STATUS_PUBLISHED,
        )
        .values('rating')
        .annotate(count=Count('id'))
    ):
        distribution[str(row['rating'])] = int(row['count'] or 0)
    return {
        'target_type': normalized_type,
        'target_id': normalized_id,
        'reviews_count': int(aggregate.get('count') or 0),
        'average_rating': _round_rating(aggregate.get('average')),
        'rating_distribution': distribution,
    }


def list_published_reviews(target_type: str, target_id: Any, *, limit: int = 50) -> list[Review]:
    normalized_type, normalized_id = normalize_target(target_type, target_id)
    return list(
        Review.objects.filter(
            target_type=normalized_type,
            target_id=normalized_id,
            status=Review.STATUS_PUBLISHED,
        ).order_by('-created_at')[:limit]
    )


def get_user_review(*, user_id: str, target_type: str, target_id: Any) -> Review | None:
    normalized_type, normalized_id = normalize_target(target_type, target_id)
    return (
        Review.objects.filter(
            target_type=normalized_type,
            target_id=normalized_id,
            author_user_id=str(user_id),
        )
        .order_by('-created_at')
        .first()
    )


def resolve_review_target(target_type: str, target_id: Any) -> dict[str, Any]:
    normalized_type, normalized_id = normalize_target(target_type, target_id)
    payload: dict[str, Any] = {
        'target_type': normalized_type,
        'target_id': normalized_id,
        'target_title': '',
        'target_slug': '',
        'trainer_id': '',
        'content': {},
    }
    if normalized_type not in CONTENT_TARGET_TYPES:
        return payload
    if normalized_type == 'course':
        try:
            from apps.trainer_cms.models import TrainerCourseDraft
            course = TrainerCourseDraft.objects.filter(id=normalized_id).first()
        except Exception:
            course = None
        if course:
            payload.update(
                {
                    'target_id': str(course.id),
                    'target_title': course.title,
                    'target_slug': course.slug,
                    'trainer_id': str(course.trainer_id),
                    'content': {
                        'id': str(course.id),
                        'source_draft_id': str(course.id),
                        'slug': course.slug,
                        'title': course.title,
                        'description': course.description,
                        'target_type': 'course',
                        'trainer_id': str(course.trainer_id),
                        'currency': course.currency,
                        'price_amount': str(course.price_amount),
                    },
                }
            )
        return payload
    try:
        from apps.entitlements.selectors import resolve_access_target
        resolved = resolve_access_target(target_type=normalized_type, target_id=normalized_id)
    except Exception:
        return payload
    content = resolved.get('content') or {}
    canonical_id = resolved.get('target_id') or normalized_id
    payload.update(
        {
            'target_id': str(canonical_id),
            'target_title': str(content.get('title') or ''),
            'target_slug': str(content.get('slug') or ''),
            'trainer_id': str(content.get('trainer_id') or ''),
            'content': content,
        }
    )
    return payload


def get_review_eligibility(*, user, target_type: str, target_id: Any) -> dict[str, Any]:
    normalized_type, normalized_id = normalize_target(target_type, target_id)
    target = resolve_review_target(normalized_type, normalized_id)
    if normalized_type not in CONTENT_TARGET_TYPES:
        return {
            'can_review': True,
            'code': 'open_target',
            'reason': 'This target type does not require purchase verification.',
            'target': target,
            'entitlement_id': None,
            'verified_purchase': False,
        }
    if not user or not getattr(user, 'is_authenticated', False):
        return {
            'can_review': False,
            'code': 'auth_required',
            'reason': 'Authentication is required to review paid content.',
            'target': target,
            'entitlement_id': None,
            'verified_purchase': False,
        }
    if target.get('trainer_id') and str(target.get('trainer_id')) == str(getattr(user, 'id', '') or ''):
        return {
            'can_review': False,
            'code': 'self_review',
            'reason': 'Trainers cannot review their own paid content.',
            'target': target,
            'entitlement_id': None,
            'verified_purchase': False,
        }
    try:
        from apps.entitlements.models import Entitlement, EntitlementTargetType
        from apps.entitlements.selectors import _active_filter, has_active_entitlement
        allowed = has_active_entitlement(user=user, target_type=normalized_type, target_id=normalized_id)
        entitlement = None
        if target.get('target_id'):
            entitlement = (
                Entitlement.objects.filter(user=user, target_type=normalized_type, target_id=target['target_id'])
                .filter(_active_filter(timezone.now()))
                .order_by('-created_at')
                .first()
            )
        if not entitlement:
            entitlement = (
                Entitlement.objects.filter(user=user, target_type=EntitlementTargetType.LIBRARY)
                .filter(_active_filter(timezone.now()))
                .order_by('-created_at')
                .first()
            )
    except Exception:
        allowed = False
        entitlement = None
    return {
        'can_review': bool(allowed),
        'code': 'verified_purchase' if allowed else 'purchase_required',
        'reason': 'Active entitlement found.' if allowed else 'Only customers with active access can review paid content.',
        'target': target,
        'entitlement_id': str(entitlement.id) if entitlement else None,
        'verified_purchase': bool(allowed),
    }


def get_trust_overview(*, days: int = 30) -> dict[str, Any]:
    days = max(1, min(int(days or 30), 365))
    since = timezone.now() - timedelta(days=days)
    base = Review.objects.all()
    period = base.filter(created_at__gte=since)
    status_counts = {
        row['status']: row['count']
        for row in base.values('status').annotate(count=Count('id')).order_by('status')
    }
    period_status_counts = {
        row['status']: row['count']
        for row in period.values('status').annotate(count=Count('id')).order_by('status')
    }
    published = base.filter(status=Review.STATUS_PUBLISHED)
    low_rating = published.filter(rating__lte=2)
    return {
        'period_days': days,
        'total_reviews': base.count(),
        'period_reviews': period.count(),
        'pending_count': status_counts.get(Review.STATUS_PENDING, 0),
        'published_count': status_counts.get(Review.STATUS_PUBLISHED, 0),
        'rejected_count': status_counts.get(Review.STATUS_REJECTED, 0),
        'flagged_count': status_counts.get(Review.STATUS_FLAGGED, 0),
        'verified_purchase_count': base.filter(verified_purchase=True).count(),
        'average_rating': _round_rating(published.aggregate(avg=Avg('rating')).get('avg')),
        'low_rating_count': low_rating.count(),
        'status_counts': status_counts,
        'period_status_counts': period_status_counts,
        'recent_low_rating': [review_to_dict(item) for item in low_rating.order_by('-created_at')[:10]],
    }


def get_trainer_quality_dashboard(*, trainer_user, days: int = 30) -> dict[str, Any]:
    days = max(1, min(int(days or 30), 365))
    since = timezone.now() - timedelta(days=days)
    trainer_id = str(getattr(trainer_user, 'id', '') or '')
    queryset = Review.objects.filter(trainer_id=trainer_id)
    period = queryset.filter(created_at__gte=since)
    published = queryset.filter(status=Review.STATUS_PUBLISHED)
    by_target: list[dict[str, Any]] = []
    for row in (
        published.values('target_type', 'target_id', 'target_title', 'target_slug')
        .annotate(count=Count('id'), average=Avg('rating'))
        .order_by('-count')[:25]
    ):
        by_target.append(
            {
                'target_type': row['target_type'],
                'target_id': row['target_id'],
                'target_title': row.get('target_title') or row['target_id'],
                'target_slug': row.get('target_slug') or '',
                'reviews_count': int(row['count'] or 0),
                'average_rating': _round_rating(row.get('average')),
            }
        )
    return {
        'period_days': days,
        'summary': {
            'total_reviews': queryset.count(),
            'period_reviews': period.count(),
            'published_count': published.count(),
            'pending_count': queryset.filter(status=Review.STATUS_PENDING).count(),
            'rejected_count': queryset.filter(status=Review.STATUS_REJECTED).count(),
            'flagged_count': queryset.filter(status=Review.STATUS_FLAGGED).count(),
            'average_rating': _round_rating(published.aggregate(avg=Avg('rating')).get('avg')),
            'low_rating_count': published.filter(rating__lte=2).count(),
        },
        'by_target': by_target,
        'recent_reviews': [review_to_dict(item) for item in queryset.order_by('-created_at')[:50]],
        'readiness': [
            {
                'code': 'has_reviews',
                'label': 'Есть опубликованные отзывы',
                'is_ok': published.exists(),
                'severity': 'success' if published.exists() else 'warning',
            },
            {
                'code': 'quality_above_four',
                'label': 'Средняя оценка 4.0+',
                'is_ok': _round_rating(published.aggregate(avg=Avg('rating')).get('avg')) >= 4.0,
                'severity': 'success' if _round_rating(published.aggregate(avg=Avg('rating')).get('avg')) >= 4.0 else 'warning',
            },
        ],
    }


def review_to_dict(review: Review) -> dict[str, Any]:
    return {
        'id': str(review.id),
        'target_type': review.target_type,
        'target_id': review.target_id,
        'target_title': review.target_title,
        'target_slug': review.target_slug,
        'trainer_id': review.trainer_id,
        'author_name': f"User {str(review.author_user_id)[:8]}",
        'rating': review.rating,
        'title': review.title,
        'body': review.body,
        'status': review.status,
        'verified_purchase': review.verified_purchase,
        'quality_flags': review.quality_flags or [],
        'moderation_note': review.moderation_note,
        'moderated_by_id': review.moderated_by_id,
        'moderated_at': review.moderated_at.isoformat() if review.moderated_at else None,
        'trainer_reply': review.trainer_reply,
        'trainer_reply_by_id': review.trainer_reply_by_id,
        'trainer_replied_at': review.trainer_replied_at.isoformat() if review.trainer_replied_at else None,
        'created_at': review.created_at.isoformat() if review.created_at else None,
        'updated_at': review.updated_at.isoformat() if getattr(review, 'updated_at', None) else None,
    }
