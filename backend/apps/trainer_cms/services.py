from django.db import transaction
from apps.content.services import ContentPublishingService
from apps.media_assets.models import MediaAsset
from apps.trainer_cms.models import (
    ContentVersion,
    PublishStatus,
    TrainerBundleDraft,
    TrainerProgramDraft,
    TrainerVideoDraft,
)


class TrainerCMSService:
    publisher = ContentPublishingService()

    @transaction.atomic
    def submit_video_for_review(self, draft: TrainerVideoDraft):
        if not draft.video_asset_id:
            raise ValueError('video asset is required')
        asset = MediaAsset.objects.get(id=draft.video_asset_id)
        if asset.upload_status != MediaAsset.UploadStatus.READY:
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
            },
            published_by_id=actor_id,
        )
        draft.current_version_number = next_version
        draft.status = PublishStatus.PUBLISHED
        draft.save(update_fields=['current_version_number', 'status', 'updated_at'])
        self.publisher.publish_program_from_draft(draft)
        return draft

    @transaction.atomic
    def publish_bundle(self, draft: TrainerBundleDraft, *, actor_id):
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
