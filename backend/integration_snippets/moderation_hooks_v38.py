"""
Integration seam examples.

Hook these calls from trainer onboarding, content publish flows, and legal/KYC review flows.
"""

from apps.moderation.services.case_management import ModerationCaseService


def open_trainer_profile_case(*, trainer, profile_id):
    return ModerationCaseService().create_case(
        target_type="trainer_profile",
        target_id=str(profile_id),
        trainer=trainer,
        queue="trainer_onboarding",
        priority=20,
        title="Trainer profile requires moderation",
        summary="Opened automatically after trainer submitted onboarding profile.",
    )


def open_content_case(*, trainer, content_id, title):
    return ModerationCaseService().create_case(
        target_type="content",
        target_id=str(content_id),
        trainer=trainer,
        queue="content_review",
        priority=30,
        title=f"Content requires review: {title}",
        summary="Opened automatically on content publish request.",
    )
