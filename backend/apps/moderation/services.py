from django.db import transaction
from apps.moderation.models import ModerationCase, ModerationDecision
from apps.trainer_cms.models import PublishStatus, TrainerVideoDraft
from apps.trainer_cms.services import TrainerCMSService


class ModerationService:
    cms_service = TrainerCMSService()

    @transaction.atomic
    def approve_video(self, moderation_case: ModerationCase, *, actor_id, comment: str = ''):
        ModerationDecision.objects.create(case=moderation_case, actor_id=actor_id, decision='approve', comment=comment)
        moderation_case.status = ModerationCase.Status.APPROVED
        moderation_case.save(update_fields=['status', 'updated_at'])
        draft = TrainerVideoDraft.objects.get(id=moderation_case.target_id)
        self.cms_service.publish_video(draft, actor_id=actor_id)
        return moderation_case

    @transaction.atomic
    def reject_video(self, moderation_case: ModerationCase, *, actor_id, comment: str):
        ModerationDecision.objects.create(case=moderation_case, actor_id=actor_id, decision='reject', comment=comment)
        moderation_case.status = ModerationCase.Status.REJECTED
        moderation_case.save(update_fields=['status', 'updated_at'])
        TrainerVideoDraft.objects.filter(id=moderation_case.target_id).update(status=PublishStatus.DRAFT)
        return moderation_case
