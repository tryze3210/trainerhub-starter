from __future__ import annotations

from apps.content.models import (
    PublishedBundle,
    PublishedBundleItem,
    PublishedLesson,
    PublishedProgram,
    PublishedVideo,
)
from apps.trainer_cms.models import (
    BundleItemDraft,
    ProgramLessonDraft,
    TrainerBundleDraft,
    TrainerProgramDraft,
    TrainerVideoDraft,
)
from apps.trainer_profiles.services import ensure_trainer_public_profile


class ContentPublishingService:
    def publish_video_from_draft(self, draft: TrainerVideoDraft):
        trainer_profile = ensure_trainer_public_profile(trainer_id=draft.trainer_id)
        obj, _ = PublishedVideo.objects.update_or_create(
            source_draft_id=draft.id,
            defaults={
                'trainer_profile': trainer_profile,
                'slug': draft.slug,
                'title': draft.title,
                'description': draft.description,
                'cover_asset_id': draft.cover_asset_id,
                'video_asset_id': draft.video_asset_id,
                'price_amount': draft.price_amount,
                'currency': draft.currency,
                'version_number': draft.current_version_number or 1,
                'is_active': True,
            },
        )
        return obj

    def publish_program_from_draft(self, draft: TrainerProgramDraft):
        trainer_profile = ensure_trainer_public_profile(trainer_id=draft.trainer_id)
        program, _ = PublishedProgram.objects.update_or_create(
            source_draft_id=draft.id,
            defaults={
                'trainer_profile': trainer_profile,
                'slug': draft.slug,
                'title': draft.title,
                'description': draft.description,
                'price_amount': draft.price_amount,
                'currency': draft.currency,
                'version_number': draft.current_version_number or 1,
                'is_active': True,
            },
        )
        existing = {str(x.source_draft_id): x for x in program.lessons.all()}
        seen = set()
        for lesson_draft in draft.lessons.all().order_by('position', 'created_at'):
            seen.add(str(lesson_draft.id))
            PublishedLesson.objects.update_or_create(
                source_draft_id=lesson_draft.id,
                defaults={
                    'program': program,
                    'slug': f'{draft.slug}-lesson-{lesson_draft.position}',
                    'title': lesson_draft.title,
                    'description': lesson_draft.description,
                    'position': lesson_draft.position,
                    'video_asset_id': lesson_draft.video_asset_id,
                    'is_preview': lesson_draft.is_preview,
                },
            )
        for source_draft_id, lesson in existing.items():
            if source_draft_id not in seen:
                lesson.delete()
        return program

    def publish_bundle_from_draft(self, draft: TrainerBundleDraft):
        trainer_profile = ensure_trainer_public_profile(trainer_id=draft.trainer_id)
        bundle, _ = PublishedBundle.objects.update_or_create(
            source_draft_id=draft.id,
            defaults={
                'trainer_profile': trainer_profile,
                'slug': draft.slug,
                'title': draft.title,
                'description': draft.description,
                'price_amount': draft.price_amount,
                'currency': draft.currency,
                'version_number': 1,
                'is_active': True,
            },
        )
        bundle.items.all().delete()
        for item in draft.items.all().order_by('position', 'created_at'):
            PublishedBundleItem.objects.create(
                bundle=bundle,
                item_type=item.item_type,
                target_slug=str(item.target_id),
                position=item.position,
            )
        return bundle
