from __future__ import annotations

from typing import Any

from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify
from rest_framework.exceptions import ValidationError

from apps.accounts.models import AccountRoleAssignment
from apps.trainer_profiles.services import ensure_trainer_public_profile
from apps.trainers.models import TrainerApplication, TrainerProfile
from apps.users.models import User


def _make_profile_slug(*, user, application: TrainerApplication) -> str:
    base = (
        application.brand_name
        or application.legal_name
        or getattr(user, "email", "").split("@", 1)[0]
        or f"trainer-{user.pk}"
    )
    slug = slugify(base) or f"trainer-{user.pk}"
    candidate = slug
    counter = 2
    while TrainerProfile.objects.filter(slug=candidate).exclude(user=user).exists():
        candidate = f"{slug}-{counter}"
        counter += 1
    return candidate


def ensure_legacy_trainer_profile_from_application(*, application: TrainerApplication) -> TrainerProfile:
    """Create/sync both trainer profile layers after admin approval.

    The current codebase still has two profile models:
    - apps.trainers.TrainerProfile for the legacy /api/v1/trainers/* dashboard API.
    - apps.trainer_profiles.TrainerPublicProfile for CMS/catalog publishing.

    Approval is the one place where both must be kept consistent.
    """
    user = application.user
    display_name = (
        application.brand_name
        or application.legal_name
        or getattr(user, "email", "").split("@", 1)[0]
        or f"Trainer {user.pk}"
    )
    slug = _make_profile_slug(user=user, application=application)

    profile, created = TrainerProfile.objects.get_or_create(
        user=user,
        defaults={
            "slug": slug,
            "display_name": display_name,
            "headline": ", ".join(application.specialties[:3]) if application.specialties else "",
            "bio": application.bio,
            "status": "active",
            "is_public": True,
        },
    )

    changed_fields: list[str] = []
    if not created:
        if not profile.display_name and display_name:
            profile.display_name = display_name
            changed_fields.append("display_name")
        if not profile.headline and application.specialties:
            profile.headline = ", ".join(application.specialties[:3])
            changed_fields.append("headline")
        if not profile.bio and application.bio:
            profile.bio = application.bio
            changed_fields.append("bio")
        if profile.status != "active":
            profile.status = "active"
            changed_fields.append("status")
        if not profile.is_public:
            profile.is_public = True
            changed_fields.append("is_public")
        if changed_fields:
            profile.save(update_fields=[*changed_fields, "updated_at"])

    public_profile = ensure_trainer_public_profile(user=user)
    public_changed_fields: list[str] = []
    sync_map = {
        "display_name": profile.display_name,
        "slug": profile.slug,
        "headline": profile.headline,
        "bio": profile.bio,
        "is_public": profile.is_public,
    }
    for field, value in sync_map.items():
        if getattr(public_profile, field) != value and value not in (None, ""):
            setattr(public_profile, field, value)
            public_changed_fields.append(field)
    if public_changed_fields:
        public_profile.save(update_fields=[*public_changed_fields, "updated_at"])

    return profile


def ensure_trainer_access_from_application(*, application: TrainerApplication) -> TrainerProfile:
    """Grant trainer role and sync both profile layers for an approved application.

    This is intentionally idempotent: admin moderation, management repair and
    future onboarding tasks can safely call it more than once.
    """
    user = application.user

    if user.role != User.Roles.TRAINER:
        user.role = User.Roles.TRAINER
        user.save(update_fields=["role", "updated_at"])

    AccountRoleAssignment.objects.get_or_create(
        user=user,
        role=AccountRoleAssignment.ROLE_USER,
        defaults={"is_active": False},
    )
    AccountRoleAssignment.objects.get_or_create(
        user=user,
        role=AccountRoleAssignment.ROLE_TRAINER,
        defaults={"is_active": True},
    )

    user.role_assignments.filter(role=AccountRoleAssignment.ROLE_USER).update(is_active=False)
    user.role_assignments.filter(role=AccountRoleAssignment.ROLE_TRAINER).update(is_active=True)

    return ensure_legacy_trainer_profile_from_application(application=application)


def normalize_moderation_decision(decision: str) -> str:
    return {
        "approve": "approved",
        "approved": "approved",
        "reject": "rejected",
        "rejected": "rejected",
        "request_changes": "needs_changes",
        "changes_requested": "needs_changes",
        "needs_changes": "needs_changes",
        "escalate": "escalated",
        "escalated": "escalated",
    }.get(decision, decision)


class TrainerApplicationService:
    def get_or_create_application(self, *, user) -> TrainerApplication:
        application, _ = TrainerApplication.objects.get_or_create(user=user)
        return application

    def get_application(self, *, user) -> TrainerApplication:
        return self.get_or_create_application(user=user)

    @transaction.atomic
    def upsert_application(self, *, user, payload: dict[str, Any]) -> TrainerApplication:
        application = self.get_or_create_application(user=user)

        for field in [
            "legal_name",
            "brand_name",
            "contact_phone",
            "country",
            "city",
            "bio",
            "experience_years",
            "specialties",
            "links",
        ]:
            if field in payload:
                setattr(application, field, payload[field])

        if application.status == TrainerApplication.Status.REJECTED:
            application.status = TrainerApplication.Status.DRAFT

        application.save()
        return application

    def _validate_submission(self, application: TrainerApplication) -> None:
        missing = []

        if not (application.brand_name or application.legal_name):
            missing.append("brand_name")

        if not application.bio:
            missing.append("bio")

        if not application.specialties:
            missing.append("specialties")

        if missing:
            raise ValidationError(
                {
                    "missing_fields": missing,
                    "detail": "Trainer application is incomplete",
                }
            )

    def _ensure_moderation_case(self, *, application: TrainerApplication):
        """Create or reuse the admin moderation case for a submitted trainer application."""
        from apps.moderation.models import ModerationCase, ModerationStatus, ModerationTargetType

        case = None
        if application.latest_moderation_case_id:
            case = ModerationCase.objects.filter(id=application.latest_moderation_case_id).first()

        if case is None:
            case = (
                ModerationCase.objects.filter(
                    queue="trainer_onboarding",
                    target_type=ModerationTargetType.TRAINER_PROFILE,
                    target_id=str(application.id),
                )
                .exclude(status=ModerationStatus.RESOLVED)
                .order_by("-opened_at")
                .first()
            )

        title_name = application.brand_name or application.legal_name or getattr(application.user, "email", "")
        summary_parts = [
            f"city={application.city}" if application.city else "",
            f"country={application.country}" if application.country else "",
            f"experience_years={application.experience_years}",
            f"specialties={', '.join(application.specialties or [])}" if application.specialties else "",
        ]
        summary = " | ".join([part for part in summary_parts if part])

        if case is None:
            case = ModerationCase.objects.create(
                target_type=ModerationTargetType.TRAINER_PROFILE,
                target_id=str(application.id),
                trainer=application.user,
                status=ModerationStatus.OPEN,
                priority=30,
                queue="trainer_onboarding",
                title=f"Trainer application: {title_name}",
                summary=summary,
            )
        else:
            changed_fields: list[str] = []
            if case.status == ModerationStatus.RESOLVED and case.latest_decision != "approved":
                case.status = ModerationStatus.OPEN
                case.resolved_at = None
                changed_fields.extend(["status", "resolved_at"])
            if case.trainer_id != application.user_id:
                case.trainer = application.user
                changed_fields.append("trainer")
            next_title = f"Trainer application: {title_name}"
            if case.title != next_title:
                case.title = next_title
                changed_fields.append("title")
            if case.summary != summary:
                case.summary = summary
                changed_fields.append("summary")
            if changed_fields:
                case.save(update_fields=[*changed_fields, "updated_at"])

        if application.latest_moderation_case_id != case.id:
            application.latest_moderation_case_id = case.id
            application.save(update_fields=["latest_moderation_case_id", "updated_at"])

        return case

    def ensure_moderation_case_for_application(self, *, application: TrainerApplication):
        return self._ensure_moderation_case(application=application)

    @transaction.atomic
    def sync_approved_application_access(self, *, application: TrainerApplication) -> TrainerApplication:
        if application.status != TrainerApplication.Status.APPROVED:
            return application

        ensure_trainer_access_from_application(application=application)
        application.moderation_snapshot = {
            **(application.moderation_snapshot or {}),
            "access_synced_at": timezone.now().isoformat(),
            "access_sync_mode": "repair_or_idempotent_admin_flow",
        }
        application.save(update_fields=["moderation_snapshot", "updated_at"])
        return application

    @transaction.atomic
    def submit_application(self, *, user, payload: dict[str, Any] | None = None) -> TrainerApplication:
        if payload:
            application = self.upsert_application(user=user, payload=payload)
        else:
            application = self.get_or_create_application(user=user)

        self._validate_submission(application)

        application.status = TrainerApplication.Status.UNDER_REVIEW
        application.submitted_at = application.submitted_at or timezone.now()
        application.moderation_snapshot = {
            **(application.moderation_snapshot or {}),
            "queue": "trainer_onboarding",
            "status": "under_review",
            "mode": "application_to_moderation_case",
            "submitted_at": application.submitted_at.isoformat(),
        }
        application.save(
            update_fields=[
                "status",
                "submitted_at",
                "moderation_snapshot",
                "updated_at",
            ]
        )
        case = self._ensure_moderation_case(application=application)
        application.moderation_snapshot = {
            **(application.moderation_snapshot or {}),
            "latest_moderation_case_id": str(case.id),
        }
        application.save(update_fields=["moderation_snapshot", "updated_at"])
        return application

    @transaction.atomic
    def apply_moderation_decision(
        self,
        *,
        application: TrainerApplication,
        decision: str,
        reviewer_note: str = "",
    ) -> TrainerApplication:
        decision = normalize_moderation_decision(decision)
        application.reviewed_at = timezone.now()
        application.reviewer_note = reviewer_note

        if decision == "approved":
            application.status = TrainerApplication.Status.APPROVED

            ensure_trainer_access_from_application(application=application)

        elif decision == "needs_changes":
            application.status = TrainerApplication.Status.CHANGES_REQUESTED
        elif decision == "rejected":
            application.status = TrainerApplication.Status.REJECTED
        else:
            application.status = TrainerApplication.Status.UNDER_REVIEW

        application.moderation_snapshot = {
            **(application.moderation_snapshot or {}),
            "decision": decision,
            "reviewed_at": application.reviewed_at.isoformat(),
            "status": application.status,
        }

        application.save(
            update_fields=[
                "status",
                "reviewed_at",
                "reviewer_note",
                "moderation_snapshot",
                "updated_at",
            ]
        )
        return application

    def sync_from_case_status(
        self,
        *,
        application: TrainerApplication,
        moderation_status: str,
    ) -> TrainerApplication:
        if moderation_status in {"open", "in_review", "escalated", "under_review"}:
            application.status = TrainerApplication.Status.UNDER_REVIEW
            application.save(update_fields=["status", "updated_at"])
        return application
