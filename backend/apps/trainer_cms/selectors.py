from apps.content.models import PublishedBundle, PublishedProgram, PublishedVideo
from apps.trainer_cms.models import TrainerBundleDraft, TrainerProgramDraft, TrainerVideoDraft


class TrainerCMSSelector:
    def list_dashboard(self, trainer_id):
        return {
            'drafts': {
                'videos': TrainerVideoDraft.objects.filter(trainer_id=trainer_id).count(),
                'programs': TrainerProgramDraft.objects.filter(trainer_id=trainer_id).count(),
                'bundles': TrainerBundleDraft.objects.filter(trainer_id=trainer_id).count(),
            },
            'published': {
                'videos': PublishedVideo.objects.filter(trainer_profile__trainer_uuid=trainer_id, is_active=True).count(),
                'programs': PublishedProgram.objects.filter(trainer_profile__trainer_uuid=trainer_id, is_active=True).count(),
                'bundles': PublishedBundle.objects.filter(trainer_profile__trainer_uuid=trainer_id, is_active=True).count(),
            },
        }
