from __future__ import annotations

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.reviews import selectors
from apps.reviews.models import Review


class ReviewService:
    @staticmethod
    @transaction.atomic
    def create_or_update_review(*, user, target_type: str, target_id: str, rating: int, title: str, body: str) -> Review:
        normalized_type, normalized_id = selectors.normalize_target(target_type, target_id)
        try:
            normalized_rating = int(rating)
        except (TypeError, ValueError):
            raise ValidationError({'rating': 'Rating must be an integer from 1 to 5'})
        if normalized_rating < 1 or normalized_rating > 5:
            raise ValidationError({'rating': 'Rating must be between 1 and 5'})
        if not title or not title.strip():
            raise ValidationError({'title': 'Title is required'})
        if not body or not body.strip():
            raise ValidationError({'body': 'Review body is required'})

        eligibility = selectors.get_review_eligibility(user=user, target_type=normalized_type, target_id=normalized_id)
        if not eligibility.get('can_review'):
            raise ValidationError({'detail': eligibility.get('reason'), 'code': eligibility.get('code')})

        target = eligibility.get('target') or {}
        canonical_id = target.get('target_id') or normalized_id
        review, created = Review.objects.get_or_create(
            target_type=normalized_type,
            target_id=str(canonical_id),
            author_user_id=str(user.id),
            defaults={
                'rating': normalized_rating,
                'title': title.strip(),
                'body': body.strip(),
                'status': Review.STATUS_PENDING,
                'verified_purchase': bool(eligibility.get('verified_purchase')),
                'entitlement_id': eligibility.get('entitlement_id') or '',
                'trainer_id': target.get('trainer_id') or '',
                'target_title': target.get('target_title') or '',
                'target_slug': target.get('target_slug') or '',
                'quality_flags': ReviewService._quality_flags(normalized_rating, body),
            },
        )
        if not created:
            review.rating = normalized_rating
            review.title = title.strip()
            review.body = body.strip()
            review.status = Review.STATUS_PENDING
            review.verified_purchase = bool(eligibility.get('verified_purchase'))
            review.entitlement_id = eligibility.get('entitlement_id') or ''
            review.trainer_id = target.get('trainer_id') or review.trainer_id or ''
            review.target_title = target.get('target_title') or review.target_title or ''
            review.target_slug = target.get('target_slug') or review.target_slug or ''
            review.quality_flags = ReviewService._quality_flags(normalized_rating, body)
            review.moderation_note = ''
            review.moderated_by_id = ''
            review.moderated_at = None
            review.save(update_fields=[
                'rating',
                'title',
                'body',
                'status',
                'verified_purchase',
                'entitlement_id',
                'trainer_id',
                'target_title',
                'target_slug',
                'quality_flags',
                'moderation_note',
                'moderated_by_id',
                'moderated_at',
                'updated_at',
            ])
        return review

    @staticmethod
    def serialize_review(review: Review) -> dict:
        return selectors.review_to_dict(review)

    @staticmethod
    @transaction.atomic
    def moderate_review(*, review: Review, decision: str, moderator=None, note: str = '') -> Review:
        normalized_decision = (decision or '').strip().lower()
        if normalized_decision == 'publish':
            review.status = Review.STATUS_PUBLISHED
        elif normalized_decision == 'reject':
            review.status = Review.STATUS_REJECTED
        elif normalized_decision == 'flag':
            review.status = Review.STATUS_FLAGGED
        else:
            raise ValidationError({'decision': 'Decision must be publish, reject or flag'})
        review.moderation_note = (note or '').strip()
        review.moderated_by_id = str(getattr(moderator, 'id', '') or '')
        review.moderated_at = timezone.now()
        review.save(update_fields=['status', 'moderation_note', 'moderated_by_id', 'moderated_at', 'updated_at'])
        ReviewService._try_audit(
            actor=moderator,
            action=f'review.{normalized_decision}',
            review=review,
            note=review.moderation_note,
        )
        return review

    @staticmethod
    def _quality_flags(rating: int, body: str) -> list[str]:
        flags: list[str] = []
        if rating <= 2:
            flags.append('low_rating')
        if len((body or '').strip()) < 40:
            flags.append('short_review')
        return flags

    @staticmethod
    def _try_audit(*, actor, action: str, review: Review, note: str = '') -> None:
        try:
            from apps.audit.models import AuditEvent
        except Exception:
            return
        try:
            AuditEvent.objects.create(
                actor_id=str(getattr(actor, 'id', '') or ''),
                action=action,
                target_type='review',
                target_id=str(review.id),
                metadata={
                    'review_status': review.status,
                    'target_type': review.target_type,
                    'target_id': review.target_id,
                    'rating': review.rating,
                    'note': note,
                },
            )
        except Exception:
            return


def build_target_reviews(target_type: str, target_id: str, *, user=None) -> dict:
    target = selectors.resolve_review_target(target_type, target_id)
    payload = {
        'summary': selectors.get_rating_summary(target['target_type'], target['target_id']),
        'items': [ReviewService.serialize_review(review) for review in selectors.list_published_reviews(target['target_type'], target['target_id'])],
        'eligibility': selectors.get_review_eligibility(user=user, target_type=target_type, target_id=target_id) if user and getattr(user, 'is_authenticated', False) else {
            'can_review': False,
            'code': 'auth_required',
            'reason': 'Authentication is required to review paid content.',
            'target': target,
            'entitlement_id': None,
            'verified_purchase': False,
        },
    }
    if user and getattr(user, 'is_authenticated', False):
        review = selectors.get_user_review(
            user_id=str(user.id),
            target_type=target['target_type'],
            target_id=target['target_id'],
        )
        payload['viewer_review'] = ReviewService.serialize_review(review) if review else None
    else:
        payload['viewer_review'] = None
    return payload
