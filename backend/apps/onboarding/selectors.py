from __future__ import annotations

from typing import Any

from apps.content.models import PublishedBundle, PublishedProgram, PublishedVideo
from apps.onboarding.models import OnboardingStepState
from apps.trainer_cms.models import (
    PublishStatus,
    TrainerBundleDraft,
    TrainerCourseDraft,
    TrainerProgramDraft,
    TrainerVideoDraft,
)
from apps.trainers.models import TrainerApplication

ONBOARDING_STEPS = [
    {
        "code": "account_basics",
        "title": "Complete account basics",
        "description": "Set display name, locale and preferred language.",
        "role_scope": "all",
        "sort_order": 10,
    },
    {
        "code": "favorites_setup",
        "title": "Choose favorite categories",
        "description": "Personalize recommendations and catalog ranking.",
        "role_scope": "user",
        "sort_order": 20,
    },
    {
        "code": "trainer_application",
        "title": "Submit trainer application",
        "description": "Send your trainer profile for moderation review.",
        "role_scope": "trainer",
        "sort_order": 30,
    },
    {
        "code": "trainer_profile",
        "title": "Create trainer profile",
        "description": "Prepare public trainer identity and positioning.",
        "role_scope": "trainer",
        "sort_order": 40,
    },
    {
        "code": "payout_setup",
        "title": "Configure payout destination",
        "description": "Required before trainer earnings can be withdrawn.",
        "role_scope": "trainer",
        "sort_order": 50,
    },
    {
        "code": "first_publish",
        "title": "Submit first content item",
        "description": "Send a draft into moderation to unlock storefront visibility.",
        "role_scope": "trainer",
        "sort_order": 60,
    },
]


def _user_roles(user) -> set[str]:
    roles = set(user.role_assignments.values_list("role", flat=True)) if hasattr(user, "role_assignments") else set()
    explicit_role = getattr(user, "role", None)
    application = getattr(user, "trainer_application", None)

    if explicit_role == "customer":
        roles.add("user")
    elif explicit_role:
        roles.add(explicit_role)

    # A user who already started a trainer application must keep seeing the trainer
    # onboarding track even before the final role switch to `trainer`.
    if application is not None:
        roles.add("trainer")

    if not roles:
        roles.add("user")
    return roles


def _visible_steps(user):
    roles = _user_roles(user)
    visible = []
    for item in sorted(ONBOARDING_STEPS, key=lambda x: x["sort_order"]):
        if item["role_scope"] == "all" or item["role_scope"] in roles:
            visible.append(item)
    return visible


def _manual_completion_map(user) -> dict[str, bool]:
    return {
        row["step_code"]: row["is_completed"]
        for row in OnboardingStepState.objects.filter(user=user).values("step_code", "is_completed")
    }


def _is_account_basics_completed(user) -> bool:
    profile = getattr(user, "account_profile", None)
    return bool(
        profile
        and (profile.full_name or "").strip()
        and (profile.timezone or "").strip()
        and (profile.preferred_language or "").strip()
    )


def _is_trainer_application_completed(user) -> bool:
    application = getattr(user, "trainer_application", None)
    return bool(
        application
        and application.status
        in {
            TrainerApplication.Status.SUBMITTED,
            TrainerApplication.Status.UNDER_REVIEW,
            TrainerApplication.Status.APPROVED,
            TrainerApplication.Status.CHANGES_REQUESTED,
        }
    )


def _is_trainer_profile_completed(user) -> bool:
    return bool(getattr(user, "trainer_profile", None) or getattr(user, "trainer_public_profile", None))


def _is_first_publish_completed(user) -> bool:
    trainer_public_profile = getattr(user, "trainer_public_profile", None)
    trainer_uuid = getattr(trainer_public_profile, "trainer_uuid", None)
    if trainer_uuid is None:
        return False
    draft_exists = (
        TrainerVideoDraft.objects.filter(trainer_id=trainer_uuid, status__in=[PublishStatus.REVIEW, PublishStatus.PUBLISHED]).exists()
        or TrainerCourseDraft.objects.filter(trainer_id=trainer_uuid, status__in=[PublishStatus.REVIEW, PublishStatus.PUBLISHED]).exists()
        or TrainerProgramDraft.objects.filter(trainer_id=trainer_uuid, status__in=[PublishStatus.REVIEW, PublishStatus.PUBLISHED]).exists()
        or TrainerBundleDraft.objects.filter(trainer_id=trainer_uuid, status__in=[PublishStatus.REVIEW, PublishStatus.PUBLISHED]).exists()
    )
    published_exists = (
        PublishedVideo.objects.filter(trainer_profile=trainer_public_profile, is_active=True).exists()
        or PublishedProgram.objects.filter(trainer_profile=trainer_public_profile, is_active=True).exists()
        or PublishedBundle.objects.filter(trainer_profile=trainer_public_profile, is_active=True).exists()
    )
    return bool(draft_exists or published_exists)


def _computed_completion(user) -> dict[str, bool]:
    settings_obj = getattr(user, "account_settings", None)
    return {
        "account_basics": _is_account_basics_completed(user),
        "favorites_setup": bool(settings_obj and settings_obj.favorite_categories),
        "trainer_application": _is_trainer_application_completed(user),
        "trainer_profile": _is_trainer_profile_completed(user),
        "first_publish": _is_first_publish_completed(user),
    }


def list_steps(*, user) -> list[dict[str, Any]]:
    manual_map = _manual_completion_map(user)
    computed_map = _computed_completion(user)
    return [
        {
            **item,
            "is_completed": manual_map.get(item["code"], computed_map.get(item["code"], False)),
        }
        for item in _visible_steps(user)
    ]


def get_step(code: str) -> dict[str, Any] | None:
    for item in ONBOARDING_STEPS:
        if item["code"] == code:
            return dict(item)
    return None


def build_status(*, user) -> dict[str, Any]:
    steps = list_steps(user=user)
    completed = len([step for step in steps if step["is_completed"]])
    total = len(steps)
    application = getattr(user, "trainer_application", None)
    return {
        "steps": steps,
        "summary": {
            "completed_steps": completed,
            "total_steps": total,
            "completion_percent": int((completed / total) * 100) if total else 0,
            "next_step": next((step["code"] for step in steps if not step["is_completed"]), None),
        },
        "trainer_application_status": getattr(application, "status", None),
    }
