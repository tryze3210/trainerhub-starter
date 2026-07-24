from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone

from apps.access_control.permissions import ROLE_TRAINER, user_role_set
from apps.trainers.models import TrainerApplication, TrainerProfile
from apps.trainers.services.applications import TrainerApplicationService
from apps.users.models import User


TERMINAL_APPLICATION_STATUSES = {
    TrainerApplication.Status.APPROVED,
    TrainerApplication.Status.REJECTED,
}

REVIEWABLE_STATUSES = {
    TrainerApplication.Status.SUBMITTED,
    TrainerApplication.Status.UNDER_REVIEW,
    TrainerApplication.Status.CHANGES_REQUESTED,
}

APPROVAL_DECISIONS = {
    "approve": "approved",
    "approved": "approved",
    "reject": "rejected",
    "rejected": "rejected",
    "request_changes": "needs_changes",
    "changes_requested": "needs_changes",
    "needs_changes": "needs_changes",
    "under_review": "under_review",
}


@dataclass(frozen=True)
class OnboardingStep:
    code: str
    title: str
    description: str
    is_completed: bool
    is_blocked: bool = False
    action_href: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "title": self.title,
            "description": self.description,
            "is_completed": self.is_completed,
            "is_blocked": self.is_blocked,
            "action_href": self.action_href,
        }


def _application_required_fields(application: TrainerApplication) -> dict[str, bool]:
    return {
        "brand_or_legal_name": bool((application.brand_name or application.legal_name or "").strip()),
        "bio": bool((application.bio or "").strip()),
        "specialties": bool(application.specialties),
        "contacts": bool((application.contact_phone or application.city or application.country or "").strip()),
    }


def _serialize_profile(profile: TrainerProfile | None) -> dict[str, Any] | None:
    if profile is None:
        return None
    return {
        "id": str(profile.id),
        "slug": profile.slug,
        "display_name": profile.display_name,
        "headline": profile.headline,
        "bio": profile.bio,
        "status": profile.status,
        "is_public": profile.is_public,
        "created_at": profile.created_at.isoformat() if profile.created_at else None,
        "updated_at": profile.updated_at.isoformat() if profile.updated_at else None,
    }


def _serialize_application(application: TrainerApplication) -> dict[str, Any]:
    required = _application_required_fields(application)
    return {
        "id": str(application.id),
        "status": application.status,
        "legal_name": application.legal_name,
        "brand_name": application.brand_name,
        "contact_phone": application.contact_phone,
        "country": application.country,
        "city": application.city,
        "specialties": application.specialties or [],
        "links": application.links or [],
        "bio": application.bio,
        "experience_years": application.experience_years,
        "submitted_at": application.submitted_at.isoformat() if application.submitted_at else None,
        "reviewed_at": application.reviewed_at.isoformat() if application.reviewed_at else None,
        "reviewer_note": application.reviewer_note,
        "latest_moderation_case_id": str(application.latest_moderation_case_id) if application.latest_moderation_case_id else None,
        "moderation_snapshot": application.moderation_snapshot or {},
        "required_fields": required,
        "is_complete": all(required.values()) or all(
            required[key] for key in ("brand_or_legal_name", "bio", "specialties")
        ),
        "created_at": application.created_at.isoformat() if application.created_at else None,
        "updated_at": application.updated_at.isoformat() if application.updated_at else None,
    }


def _has_active_trainer_role(user: User) -> bool:
    return ROLE_TRAINER in user_role_set(user)


def _legacy_role_label(user: User) -> str | None:
    return user.role


def get_trainer_onboarding_state(*, user: User) -> dict[str, Any]:
    service = TrainerApplicationService()
    application = service.get_application(user=user)
    profile = getattr(user, "trainer_profile", None)
    required = _application_required_fields(application)
    application_ready = all(required[key] for key in ("brand_or_legal_name", "bio", "specialties"))
    application_submitted = application.status in {
        TrainerApplication.Status.SUBMITTED,
        TrainerApplication.Status.UNDER_REVIEW,
        TrainerApplication.Status.APPROVED,
        TrainerApplication.Status.CHANGES_REQUESTED,
        TrainerApplication.Status.REJECTED,
    }
    application_approved = application.status == TrainerApplication.Status.APPROVED
    has_trainer_role = _has_active_trainer_role(user)
    profile_ready = bool(profile and profile.slug and profile.display_name and profile.status == "active")
    dashboard_unlocked = bool(application_approved and has_trainer_role and profile_ready)

    steps = [
        OnboardingStep(
            code="application_draft",
            title="Заполнить заявку",
            description="Brand/legal name, bio и specialties обязательны перед отправкой на модерацию.",
            is_completed=application_ready,
            action_href="/trainer/onboarding",
        ),
        OnboardingStep(
            code="application_submit",
            title="Отправить заявку",
            description="После отправки заявка попадает в admin moderation queue.",
            is_completed=application_submitted,
            is_blocked=not application_ready,
            action_href="/trainer/onboarding",
        ),
        OnboardingStep(
            code="admin_review",
            title="Пройти проверку администратора",
            description="Admin approve создаёт/sync trainer profile и выдаёт trainer role.",
            is_completed=application_approved,
            is_blocked=not application_submitted,
            action_href="/trainer/application-status",
        ),
        OnboardingStep(
            code="dashboard_unlock",
            title="Разблокировать trainer dashboard",
            description="Dashboard открывается только после approve, trainer role и active profile.",
            is_completed=dashboard_unlocked,
            is_blocked=not application_approved,
            action_href="/trainer/dashboard",
        ),
        OnboardingStep(
            code="first_publish",
            title="Подготовить первый продукт",
            description="После approve можно собирать продукты, видео, bundles и продажи.",
            is_completed=False,
            is_blocked=not dashboard_unlocked,
            action_href="/trainer/dashboard/products",
        ),
    ]
    completed_count = sum(1 for step in steps if step.is_completed)
    next_step = next((step for step in steps if not step.is_completed), steps[-1])

    return {
        "user": {
            "id": str(user.id),
            "email": user.email,
            "role": _legacy_role_label(user),
            "is_staff": bool(user.is_staff),
        },
        "application": _serialize_application(application),
        "profile": _serialize_profile(profile),
        "dashboard_unlocked": dashboard_unlocked,
        "can_submit_application": application_ready and application.status not in TERMINAL_APPLICATION_STATUSES,
        "can_edit_application": application.status in {
            TrainerApplication.Status.DRAFT,
            TrainerApplication.Status.CHANGES_REQUESTED,
            TrainerApplication.Status.REJECTED,
        },
        "can_access_content_studio": dashboard_unlocked,
        "summary": {
            "total_steps": len(steps),
            "completed_steps": completed_count,
            "completion_percent": int(round((completed_count / len(steps)) * 100)),
            "next_step": next_step.code,
            "next_step_title": next_step.title,
            "status": "unlocked" if dashboard_unlocked else application.status,
        },
        "steps": [step.as_dict() for step in steps],
    }


def list_trainer_applications(*, status_filter: str | None = None, search: str | None = None, limit: int = 100) -> dict[str, Any]:
    queryset = TrainerApplication.objects.select_related("user").order_by("-submitted_at", "-created_at")
    if status_filter:
        queryset = queryset.filter(status=status_filter)
    if search:
        queryset = queryset.filter(
            Q(user__email__icontains=search)
            | Q(legal_name__icontains=search)
            | Q(brand_name__icontains=search)
            | Q(city__icontains=search)
        )
    limit = max(1, min(int(limit or 100), 250))
    results = list(queryset[:limit])
    return {
        "count": queryset.count(),
        "limit": limit,
        "results": [serialize_admin_application(application) for application in results],
    }


def serialize_admin_application(application: TrainerApplication) -> dict[str, Any]:
    profile = getattr(application.user, "trainer_profile", None)
    return {
        **_serialize_application(application),
        "user": {
            "id": str(application.user_id),
            "email": application.user.email,
            "role": application.user.role,
            "is_active": application.user.is_active,
            "is_staff": application.user.is_staff,
        },
        "profile": _serialize_profile(profile),
        "reviewable": application.status in REVIEWABLE_STATUSES,
        "admin_hrefs": {
            "detail": f"/api/v1/trainers/admin/applications/{application.id}/",
            "review": f"/api/v1/trainers/admin/applications/{application.id}/review/",
            "sync_access": f"/api/v1/trainers/admin/applications/{application.id}/sync-access/",
        },
    }


@transaction.atomic
def review_trainer_application(
    *,
    application_id: str,
    decision: str,
    reviewer_note: str = "",
    reviewer: User | None = None,
) -> dict[str, Any]:
    application = get_object_or_404(TrainerApplication.objects.select_related("user"), id=application_id)
    normalized_decision = APPROVAL_DECISIONS.get(decision, decision)
    service = TrainerApplicationService()

    if normalized_decision == "under_review":
        application.status = TrainerApplication.Status.UNDER_REVIEW
        application.reviewer_note = reviewer_note
        application.reviewed_at = timezone.now()
        application.moderation_snapshot = {
            **(application.moderation_snapshot or {}),
            "decision": "under_review",
            "reviewed_at": application.reviewed_at.isoformat(),
            "reviewer_id": str(reviewer.id) if reviewer else None,
            "reviewer_email": reviewer.email if reviewer else None,
        }
        application.save(update_fields=["status", "reviewer_note", "reviewed_at", "moderation_snapshot", "updated_at"])
    else:
        application = service.apply_moderation_decision(
            application=application,
            decision=normalized_decision,
            reviewer_note=reviewer_note,
        )
        application.moderation_snapshot = {
            **(application.moderation_snapshot or {}),
            "reviewer_id": str(reviewer.id) if reviewer else None,
            "reviewer_email": reviewer.email if reviewer else None,
            "review_source": "trainer_onboarding_admin_api",
        }
        application.save(update_fields=["moderation_snapshot", "updated_at"])

    if application.status == TrainerApplication.Status.APPROVED:
        application = service.sync_approved_application_access(application=application)

    return {
        "application": serialize_admin_application(application),
        "onboarding_state": get_trainer_onboarding_state(user=application.user),
    }


@transaction.atomic
def sync_approved_trainer_access(*, application_id: str) -> dict[str, Any]:
    application = get_object_or_404(TrainerApplication.objects.select_related("user"), id=application_id)
    service = TrainerApplicationService()
    application = service.sync_approved_application_access(application=application)
    return {
        "application": serialize_admin_application(application),
        "onboarding_state": get_trainer_onboarding_state(user=application.user),
    }
