from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from django.db import transaction

from apps.accounts.models import AccountRoleAssignment
from apps.moderation.models import ModerationCase, ModerationStatus
from apps.trainer_profiles.models import TrainerPublicProfile
from apps.trainers.models import TrainerApplication, TrainerProfile
from apps.trainers.services.applications import TrainerApplicationService
from apps.users.models import User


REVIEWABLE_APPLICATION_STATUSES = {
    TrainerApplication.Status.SUBMITTED,
    TrainerApplication.Status.UNDER_REVIEW,
}


@dataclass(frozen=True)
class MarketplaceRepairReport:
    dry_run: bool
    inspected_applications: int
    reviewable_applications: int
    approved_applications: int
    moderation_cases_created: int
    moderation_cases_relinked: int
    approved_access_synced: int
    stale_case_links_found: int
    errors: list[dict[str, Any]]

    def as_dict(self) -> dict[str, Any]:
        return {
            "dry_run": self.dry_run,
            "inspected_applications": self.inspected_applications,
            "reviewable_applications": self.reviewable_applications,
            "approved_applications": self.approved_applications,
            "moderation_cases_created": self.moderation_cases_created,
            "moderation_cases_relinked": self.moderation_cases_relinked,
            "approved_access_synced": self.approved_access_synced,
            "stale_case_links_found": self.stale_case_links_found,
            "errors": self.errors,
        }


class TrainerMarketplaceMaintenanceService:
    """Operational repair/backfill service for trainer marketplace core.

    The service is deliberately idempotent and has a dry-run mode so it can be
    used both from a management command and from a staff-only admin endpoint.
    """

    application_service = TrainerApplicationService()

    def inspect(self) -> dict[str, Any]:
        total = TrainerApplication.objects.count()
        reviewable = TrainerApplication.objects.filter(status__in=REVIEWABLE_APPLICATION_STATUSES).count()
        approved = TrainerApplication.objects.filter(status=TrainerApplication.Status.APPROVED).count()

        reviewable_without_case = 0
        reviewable_with_stale_case = 0
        for application in TrainerApplication.objects.filter(status__in=REVIEWABLE_APPLICATION_STATUSES).only(
            "id", "latest_moderation_case_id", "status"
        ):
            if not application.latest_moderation_case_id:
                reviewable_without_case += 1
                continue
            if not ModerationCase.objects.filter(id=application.latest_moderation_case_id).exists():
                reviewable_with_stale_case += 1

        approved_without_legacy_profile = 0
        approved_without_public_profile = 0
        approved_without_trainer_role = 0
        approved_without_active_role_assignment = 0
        approved_qs = TrainerApplication.objects.filter(status=TrainerApplication.Status.APPROVED).select_related("user")
        for application in approved_qs:
            user = application.user
            if not TrainerProfile.objects.filter(user=user).exists():
                approved_without_legacy_profile += 1
            if not TrainerPublicProfile.objects.filter(user=user).exists():
                approved_without_public_profile += 1
            if user.role != User.Roles.TRAINER:
                approved_without_trainer_role += 1
            if not AccountRoleAssignment.objects.filter(
                user=user,
                role=AccountRoleAssignment.ROLE_TRAINER,
                is_active=True,
            ).exists():
                approved_without_active_role_assignment += 1

        return {
            "trainer_applications": {
                "total": total,
                "reviewable": reviewable,
                "approved": approved,
                "reviewable_without_case": reviewable_without_case,
                "reviewable_with_stale_case": reviewable_with_stale_case,
                "approved_without_legacy_profile": approved_without_legacy_profile,
                "approved_without_public_profile": approved_without_public_profile,
                "approved_without_trainer_role": approved_without_trainer_role,
                "approved_without_active_role_assignment": approved_without_active_role_assignment,
            },
            "moderation": {
                "open_onboarding_cases": ModerationCase.objects.filter(
                    queue="trainer_onboarding",
                    status__in=[ModerationStatus.OPEN, ModerationStatus.IN_REVIEW, ModerationStatus.ESCALATED],
                ).count(),
                "resolved_onboarding_cases": ModerationCase.objects.filter(
                    queue="trainer_onboarding",
                    status=ModerationStatus.RESOLVED,
                ).count(),
            },
        }

    @transaction.atomic
    def repair(self, *, dry_run: bool = True) -> MarketplaceRepairReport:
        inspected = 0
        reviewable_count = 0
        approved_count = 0
        cases_created = 0
        cases_relinked = 0
        approved_synced = 0
        stale_links = 0
        errors: list[dict[str, Any]] = []

        reviewable_qs = TrainerApplication.objects.select_related("user").filter(status__in=REVIEWABLE_APPLICATION_STATUSES)
        for application in reviewable_qs:
            inspected += 1
            reviewable_count += 1
            had_case_id = application.latest_moderation_case_id
            if had_case_id and not ModerationCase.objects.filter(id=had_case_id).exists():
                stale_links += 1

            try:
                if dry_run:
                    existing_case = None
                    if application.latest_moderation_case_id:
                        existing_case = ModerationCase.objects.filter(id=application.latest_moderation_case_id).first()
                    if existing_case is None:
                        candidate = ModerationCase.objects.filter(
                            queue="trainer_onboarding",
                            target_id=str(application.id),
                        ).exclude(status=ModerationStatus.RESOLVED).first()
                        if candidate is None:
                            cases_created += 1
                        elif application.latest_moderation_case_id != candidate.id:
                            cases_relinked += 1
                    continue

                before_case_id = application.latest_moderation_case_id
                case = self.application_service.ensure_moderation_case_for_application(application=application)
                if before_case_id is None:
                    cases_created += 1
                elif before_case_id != case.id:
                    cases_relinked += 1
            except Exception as exc:  # pragma: no cover - operational report path
                errors.append({"application_id": str(application.id), "error": str(exc)})

        approved_qs = TrainerApplication.objects.select_related("user").filter(status=TrainerApplication.Status.APPROVED)
        for application in approved_qs:
            inspected += 1
            approved_count += 1
            needs_sync = (
                application.user.role != User.Roles.TRAINER
                or not TrainerProfile.objects.filter(user=application.user).exists()
                or not TrainerPublicProfile.objects.filter(user=application.user).exists()
                or not AccountRoleAssignment.objects.filter(
                    user=application.user,
                    role=AccountRoleAssignment.ROLE_TRAINER,
                    is_active=True,
                ).exists()
            )
            if not needs_sync:
                continue
            approved_synced += 1
            if dry_run:
                continue
            try:
                self.application_service.sync_approved_application_access(application=application)
            except Exception as exc:  # pragma: no cover - operational report path
                errors.append({"application_id": str(application.id), "error": str(exc)})

        return MarketplaceRepairReport(
            dry_run=dry_run,
            inspected_applications=inspected,
            reviewable_applications=reviewable_count,
            approved_applications=approved_count,
            moderation_cases_created=cases_created,
            moderation_cases_relinked=cases_relinked,
            approved_access_synced=approved_synced,
            stale_case_links_found=stale_links,
            errors=errors,
        )
