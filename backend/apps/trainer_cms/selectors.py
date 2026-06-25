from apps.content.models import PublishedBundle, PublishedProgram, PublishedVideo
from apps.trainer_cms.models import (
    PublishStatus,
    TrainerBundleDraft,
    TrainerCourseDraft,
    TrainerProgramDraft,
    TrainerVideoDraft,
)
from apps.trainers.models import TrainerApplication


def _safe_onboarding_summary(user):
    try:
        from apps.onboarding import selectors as onboarding_selectors

        payload = onboarding_selectors.build_status(user=user)
        return payload.get(
            "summary",
            {
                "completed_steps": 0,
                "total_steps": 0,
                "completion_percent": 0,
                "next_step": None,
            },
        )
    except Exception:
        return {
            "completed_steps": 0,
            "total_steps": 0,
            "completion_percent": 0,
            "next_step": None,
        }


class TrainerCMSSelector:
    def list_dashboard(self, trainer_id):
        draft_videos = TrainerVideoDraft.objects.filter(trainer_id=trainer_id)
        draft_courses = TrainerCourseDraft.objects.filter(trainer_id=trainer_id)
        draft_programs = TrainerProgramDraft.objects.filter(trainer_id=trainer_id)
        draft_bundles = TrainerBundleDraft.objects.filter(trainer_id=trainer_id)

        published_videos = PublishedVideo.objects.filter(
            trainer_profile__trainer_uuid=trainer_id,
            is_active=True,
        )
        published_programs = PublishedProgram.objects.filter(
            trainer_profile__trainer_uuid=trainer_id,
            is_active=True,
        )
        published_bundles = PublishedBundle.objects.filter(
            trainer_profile__trainer_uuid=trainer_id,
            is_active=True,
        )

        application = TrainerApplication.objects.filter(user_id=trainer_id).first()

        pending_review_count = draft_videos.filter(status=PublishStatus.REVIEW).count()
        if application and application.status in {
            TrainerApplication.Status.SUBMITTED,
            TrainerApplication.Status.UNDER_REVIEW,
            TrainerApplication.Status.CHANGES_REQUESTED,
        }:
            pending_review_count += 1

        onboarding_summary = _safe_onboarding_summary(application.user) if application else {
            "completed_steps": 0,
            "total_steps": 0,
            "completion_percent": 0,
            "next_step": None,
        }

        return {
            "drafts": {
                "videos": draft_videos.count(),
                "courses": draft_courses.count(),
                "programs": draft_programs.count(),
                "bundles": draft_bundles.count(),
            },
            "published": {
                "videos": published_videos.count(),
                "programs": published_programs.count(),
                "bundles": published_bundles.count(),
            },
            "moderation": {
                "open_cases_count": 0,
                "risk_flags_count": 0,
            },
            "application": {
                "status": getattr(application, "status", None),
                "submitted_at": getattr(application, "submitted_at", None),
                "reviewed_at": getattr(application, "reviewed_at", None),
                "reviewer_note": getattr(application, "reviewer_note", ""),
                "latest_moderation_case_id": str(application.latest_moderation_case_id)
                if getattr(application, "latest_moderation_case_id", None)
                else None,
            }
            if application
            else None,
            "onboarding": onboarding_summary,
            "draft_videos_count": draft_videos.count(),
            "draft_courses_count": draft_courses.count(),
            "published_videos_count": published_videos.count(),
            "draft_programs_count": draft_programs.count(),
            "published_programs_count": published_programs.count(),
            "draft_bundles_count": draft_bundles.count(),
            "published_bundles_count": published_bundles.count(),
            "pending_review_count": pending_review_count,
            "total_sales_count": 0,
        }
