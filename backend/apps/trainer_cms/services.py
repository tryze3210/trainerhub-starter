from django.db import transaction
from apps.content.services import ContentPublishingService
from apps.videos.models import MediaAsset
from apps.trainer_cms.models import (
    ContentVersion,
    PublishStatus,
    TrainerBundleDraft,
    TrainerCourseDraft,
    TrainerProgramDraft,
    TrainerVideoDraft,
)


class TrainerCMSService:
    publisher = ContentPublishingService()

    @transaction.atomic
    def submit_video_for_review(self, draft: TrainerVideoDraft):
        if not draft.video_asset_id:
            raise ValueError('video asset is required')
        asset = MediaAsset.objects.get(id=draft.video_asset_id, is_deleted=False)
        if asset.status != MediaAsset.Status.VERIFIED:
            raise ValueError('video asset is not ready')
        draft.status = PublishStatus.REVIEW
        draft.save(update_fields=['status', 'updated_at'])
        return draft

    @transaction.atomic
    def publish_video(self, draft: TrainerVideoDraft, *, actor_id):
        next_version = draft.current_version_number + 1
        snapshot = {
            'title': draft.title,
            'slug': draft.slug,
            'description': draft.description,
            'video_asset_id': str(draft.video_asset_id) if draft.video_asset_id else None,
            'cover_asset_id': str(draft.cover_asset_id) if draft.cover_asset_id else None,
            'price_amount': str(draft.price_amount),
            'currency': draft.currency,
        }
        ContentVersion.objects.create(
            trainer_id=draft.trainer_id,
            entity_type=ContentVersion.EntityType.VIDEO,
            entity_id=draft.id,
            version_number=next_version,
            snapshot=snapshot,
            published_by_id=actor_id,
        )
        draft.current_version_number = next_version
        draft.status = PublishStatus.PUBLISHED
        draft.save(update_fields=['current_version_number', 'status', 'updated_at'])
        self.publisher.publish_video_from_draft(draft)
        return draft

    @transaction.atomic
    def publish_program(self, draft: TrainerProgramDraft, *, actor_id):
        lessons = list(draft.lessons.order_by('position', 'created_at'))
        lesson_count = len(lessons)
        if lesson_count == 0:
            raise ValueError('program requires at least one lesson before publish')
        if any(not lesson.video_asset_id for lesson in lessons):
            raise ValueError('each lesson must reference a verified video asset before publish')
        next_version = draft.current_version_number + 1
        ContentVersion.objects.create(
            trainer_id=draft.trainer_id,
            entity_type=ContentVersion.EntityType.PROGRAM,
            entity_id=draft.id,
            version_number=next_version,
            snapshot={
                'title': draft.title,
                'slug': draft.slug,
                'description': draft.description,
                'price_amount': str(draft.price_amount),
                'currency': draft.currency,
                'lesson_count': lesson_count,
            },
            published_by_id=actor_id,
        )
        draft.current_version_number = next_version
        draft.status = PublishStatus.PUBLISHED
        draft.save(update_fields=['current_version_number', 'status', 'updated_at'])
        self.publisher.publish_program_from_draft(draft)
        return draft

    @transaction.atomic
    def publish_course(self, draft: TrainerCourseDraft, *, actor_id):
        lessons = list(draft.lessons.order_by('position', 'created_at'))
        lesson_count = len(lessons)
        if lesson_count == 0:
            raise ValueError('course requires at least one lesson before publish')
        if any(not lesson.video_asset_id for lesson in lessons):
            raise ValueError('each course lesson must reference a video asset before publish')
        next_version = draft.current_version_number + 1
        ContentVersion.objects.create(
            trainer_id=draft.trainer_id,
            entity_type=ContentVersion.EntityType.COURSE,
            entity_id=draft.id,
            version_number=next_version,
            snapshot={
                'title': draft.title,
                'slug': draft.slug,
                'description': draft.description,
                'price_amount': str(draft.price_amount),
                'currency': draft.currency,
                'lesson_count': lesson_count,
                'materials_count': sum(len(lesson.materials or []) for lesson in lessons),
                'metadata': draft.metadata,
            },
            published_by_id=actor_id,
        )
        draft.current_version_number = next_version
        draft.status = PublishStatus.PUBLISHED
        draft.save(update_fields=['current_version_number', 'status', 'updated_at'])
        return draft

    @transaction.atomic
    def publish_bundle(self, draft: TrainerBundleDraft, *, actor_id):
        items = list(draft.items.order_by('position', 'created_at'))
        item_count = len(items)
        if item_count == 0:
            raise ValueError('bundle requires at least one item before publish')
        ContentVersion.objects.create(
            trainer_id=draft.trainer_id,
            entity_type=ContentVersion.EntityType.BUNDLE,
            entity_id=draft.id,
            version_number=1,
            snapshot={
                'title': draft.title,
                'slug': draft.slug,
                'description': draft.description,
                'price_amount': str(draft.price_amount),
                'currency': draft.currency,
                'items_count': item_count,
            },
            published_by_id=actor_id,
        )
        draft.status = PublishStatus.PUBLISHED
        draft.save(update_fields=['status', 'updated_at'])
        self.publisher.publish_bundle_from_draft(draft)
        return draft

    @transaction.atomic
    def archive_video(self, draft: TrainerVideoDraft):
        draft.status = PublishStatus.ARCHIVED
        draft.save(update_fields=['status', 'updated_at'])
        return draft
