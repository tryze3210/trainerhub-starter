from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Any

from django.db.models import Q
from django.utils import timezone

from apps.access_control.permissions import ROLE_TRAINER, user_role_set
from apps.trainers.models import TrainerApplication, TrainerProfile
from apps.trainers.onboarding_flow import serialize_admin_application
from apps.users.models import User


READINESS_API_SURFACE = {
    "candidate": [
        "/api/v1/trainers/me/application/",
        "/api/v1/trainers/me/application/submit/",
        "/api/v1/trainers/me/application-status/",
        "/api/v1/trainers/me/onboarding/status/",
    ],
    "admin": [
        "/api/v1/trainers/admin/applications/",
        "/api/v1/trainers/admin/applications/{application_id}/",
        "/api/v1/trainers/admin/applications/{application_id}/review/",
        "/api/v1/trainers/admin/applications/{application_id}/sync-access/",
        "/api/v1/trainers/admin/applications/readiness/",
    ],
    "trainer_after_approval": [
        "/api/v1/trainers/me/profile/",
        "/api/v1/trainers/me/revenue/summary/",
        "/api/v1/trainers/me/analytics/overview/",
    ],
}


REVIEW_QUEUE_STATUSES = {
    TrainerApplication.Status.SUBMITTED,
    TrainerApplication.Status.UNDER_REVIEW,
}

BLOCKED_STATUSES = {
    TrainerApplication.Status.REJECTED,
    TrainerApplication.Status.CHANGES_REQUESTED,
}


@dataclass(frozen=True)
class TrainerApplicationReadinessIssue:
    code: str
    severity: str
    message: str
    application: TrainerApplication
    details: dict[str, Any]
    remediation: str

    def as_dict(self, *, include_sample: bool) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "code": self.code,
            "severity": self.severity,
            "message": self.message,
            "application_id": str(self.application.id),
            "user_id": str(self.application.user_id),
            "user_email": self.application.user.email,
            "application_status": self.application.status,
            "details": self.details,
            "remediation": self.remediation,
        }
        if include_sample:
            payload["application"] = serialize_admin_application(self.application)
        return payload


def _trainer_role_value() -> str:
    return getattr(getattr(User, "Roles", object), "TRAINER", "trainer")


def _application_required_fields(application: TrainerApplication) -> dict[str, bool]:
    return {
        "brand_or_legal_name": bool((application.brand_name or application.legal_name or "").strip()),
        "bio": bool((application.bio or "").strip()),
        "specialties": bool(application.specialties),
        "contacts": bool((application.contact_phone or application.city or application.country or "").strip()),
    }


def _application_is_complete(application: TrainerApplication) -> bool:
    required = _application_required_fields(application)
    return all(required[key] for key in ("brand_or_legal_name", "bio", "specialties"))


def _profile_state(profile: TrainerProfile | None) -> dict[str, Any]:
    if profile is None:
        return {
            "exists": False,
            "active": False,
            "public": False,
            "has_slug": False,
            "has_display_name": False,
        }
    return {
        "exists": True,
        "id": str(profile.id),
        "slug": profile.slug,
        "display_name": profile.display_name,
        "status": profile.status,
        "is_public": profile.is_public,
        "active": profile.status == "active",
        "public": bool(profile.is_public),
        "has_slug": bool(profile.slug),
        "has_display_name": bool(profile.display_name),
    }


def _has_active_trainer_assignment(user: User) -> bool | None:
    try:
        return bool(user.role_assignments.filter(role="trainer", is_active=True).exists())
    except Exception:
        return None


def _has_runtime_trainer_role(user: User) -> bool:
    return ROLE_TRAINER in user_role_set(user)


def _issue(
    *,
    code: str,
    severity: str,
    message: str,
    application: TrainerApplication,
    remediation: str,
    **details: Any,
) -> TrainerApplicationReadinessIssue:
    return TrainerApplicationReadinessIssue(
        code=code,
        severity=severity,
        message=message,
        application=application,
        details=details,
        remediation=remediation,
    )


def _detect_access_sync_issues(application: TrainerApplication) -> list[TrainerApplicationReadinessIssue]:
    issues: list[TrainerApplicationReadinessIssue] = []
    if application.status != TrainerApplication.Status.APPROVED:
        return issues

    user = application.user
    profile = getattr(user, "trainer_profile", None)
    profile_payload = _profile_state(profile)
    trainer_role = _trainer_role_value()
    has_role = getattr(user, "role", None) == trainer_role
    has_assignment = _has_active_trainer_assignment(user)

    if not has_role:
        issues.append(
            _issue(
                code="approved_without_trainer_role",
                severity="critical",
                message="Approved trainer application has not granted the trainer user role.",
                application=application,
                remediation="Run admin application sync-access or re-approve the application to call TrainerApplicationService.sync_approved_application_access().",
                user_role=getattr(user, "role", None),
                expected_role=trainer_role,
            )
        )
    if has_assignment is False:
        issues.append(
            _issue(
                code="approved_without_active_trainer_assignment",
                severity="warning",
                message="Approved trainer application has no active AccountRoleAssignment for trainer.",
                application=application,
                remediation="Run sync-access for the application to repair role assignments.",
            )
        )
    if profile is None:
        issues.append(
            _issue(
                code="approved_without_trainer_profile",
                severity="critical",
                message="Approved trainer application has no legacy TrainerProfile.",
                application=application,
                remediation="Run admin application sync-access to create/sync trainer profile layers.",
                profile=profile_payload,
            )
        )
    elif not all(
        [
            profile_payload["active"],
            profile_payload["public"],
            profile_payload["has_slug"],
            profile_payload["has_display_name"],
        ]
    ):
        issues.append(
            _issue(
                code="approved_profile_not_dashboard_ready",
                severity="warning",
                message="Approved trainer profile exists but is not dashboard-ready.",
                application=application,
                remediation="Run sync-access and verify profile status, slug, display_name and visibility.",
                profile=profile_payload,
            )
        )
    return issues


def _detect_review_queue_issues(
    application: TrainerApplication,
    *,
    stale_after_days: int,
    now,
) -> list[TrainerApplicationReadinessIssue]:
    issues: list[TrainerApplicationReadinessIssue] = []
    if application.status in REVIEW_QUEUE_STATUSES and not _application_is_complete(application):
        issues.append(
            _issue(
                code="review_queue_incomplete_application",
                severity="warning",
                message="Application is in review queue but required candidate fields are incomplete.",
                application=application,
                remediation="Request changes or let the candidate complete brand/legal name, bio and specialties before review.",
                required_fields=_application_required_fields(application),
            )
        )

    review_started_at = application.submitted_at or application.updated_at or application.created_at
    if application.status in REVIEW_QUEUE_STATUSES and review_started_at:
        age_days = max(0, (now - review_started_at).days)
        if age_days >= stale_after_days:
            issues.append(
                _issue(
                    code="stale_trainer_application_review",
                    severity="warning",
                    message="Trainer application has been waiting in review queue longer than the allowed threshold.",
                    application=application,
                    remediation="Admin should approve, request changes, reject, or explicitly keep it under review.",
                    age_days=age_days,
                    stale_after_days=stale_after_days,
                    review_started_at=review_started_at.isoformat(),
                )
            )
    return issues


def _detect_terminal_state_issues(application: TrainerApplication) -> list[TrainerApplicationReadinessIssue]:
    issues: list[TrainerApplicationReadinessIssue] = []
    if application.status in BLOCKED_STATUSES and not (application.reviewer_note or "").strip():
        issues.append(
            _issue(
                code="blocked_application_without_reviewer_note",
                severity="info",
                message="Rejected or changes-requested application has no reviewer note for the candidate.",
                application=application,
                remediation="Add an actionable reviewer_note when rejecting or requesting changes.",
            )
        )
    if application.status == TrainerApplication.Status.APPROVED and not application.reviewed_at:
        issues.append(
            _issue(
                code="approved_application_without_reviewed_at",
                severity="info",
                message="Approved trainer application has no reviewed_at timestamp.",
                application=application,
                remediation="Re-run admin review/sync flow to stamp review metadata for auditability.",
            )
        )
    return issues


def _detect_duplicate_profile_slugs() -> list[dict[str, Any]]:
    # Slug is unique at the DB model level in the expected schema. This check remains useful as a readiness guard
    # for older databases, manual imports, or partially restored fixtures.
    duplicates: list[dict[str, Any]] = []
    seen: set[str] = set()
    for slug in TrainerProfile.objects.exclude(slug="").values_list("slug", flat=True):
        if slug in seen:
            duplicates.append({"slug": slug})
        seen.add(slug)
    return duplicates


def build_trainer_application_readiness(
    *,
    limit: int = 50,
    stale_after_days: int = 7,
    include_samples: bool = True,
    include_recommendations: bool = True,
) -> dict[str, Any]:
    now = timezone.now()
    limit = max(1, min(int(limit or 50), 250))
    stale_after_days = max(1, min(int(stale_after_days or 7), 90))

    queryset = TrainerApplication.objects.select_related("user").order_by("-updated_at", "-created_at")
    applications = list(queryset)
    status_counts = Counter(application.status for application in applications)

    issues: list[TrainerApplicationReadinessIssue] = []
    for application in applications:
        issues.extend(_detect_access_sync_issues(application))
        issues.extend(_detect_review_queue_issues(application, stale_after_days=stale_after_days, now=now))
        issues.extend(_detect_terminal_state_issues(application))

    duplicate_profile_slugs = _detect_duplicate_profile_slugs()
    for duplicate in duplicate_profile_slugs:
        # Profile slug duplicates are expected to be impossible with the current schema; expose them separately
        # because they are profile integrity issues, not application-row issues.
        duplicate["severity"] = "critical"
        duplicate["code"] = "duplicate_trainer_profile_slug"
        duplicate["message"] = "Duplicate trainer profile slug detected. Public storefront routing is ambiguous."

    severity_counts = Counter(issue.severity for issue in issues)
    severity_counts.update(issue["severity"] for issue in duplicate_profile_slugs)

    critical_count = severity_counts.get("critical", 0)
    warning_count = severity_counts.get("warning", 0)
    info_count = severity_counts.get("info", 0)
    total_issues = critical_count + warning_count + info_count
    if critical_count:
        status = "degraded"
    elif warning_count:
        status = "warning"
    elif queryset.count() == 0:
        status = "empty"
    else:
        status = "healthy"

    approved_queryset = queryset.filter(status=TrainerApplication.Status.APPROVED)
    dashboard_ready_count = 0
    for application in approved_queryset:
        profile = getattr(application.user, "trainer_profile", None)
        if (
            _has_runtime_trainer_role(application.user)
            and profile is not None
            and profile.status == "active"
            and profile.slug
            and profile.display_name
        ):
            dashboard_ready_count += 1

    issue_payloads = [issue.as_dict(include_sample=include_samples) for issue in issues[:limit]]
    issue_payloads.extend(duplicate_profile_slugs[: max(0, limit - len(issue_payloads))])

    recommendations: list[str] = []
    if critical_count:
        recommendations.append("Run sync-access for approved applications with missing trainer role/profile before allowing content publishing.")
    if warning_count:
        recommendations.append("Review stale or incomplete applications and either approve, reject, or request changes with reviewer notes.")
    if status == "empty":
        recommendations.append("No trainer applications exist yet. Keep onboarding routes enabled and verify public CTA links point to /trainer/onboarding.")
    if not recommendations:
        recommendations.append("Trainer onboarding looks ready. Continue monitoring review queue age and approved profile sync.")

    return {
        "status": status,
        "generated_at": now.isoformat(),
        "summary": {
            "total_applications": queryset.count(),
            "by_status": {status_key: status_counts.get(status_key, 0) for status_key, _ in TrainerApplication.Status.choices},
            "review_queue_count": queryset.filter(status__in=REVIEW_QUEUE_STATUSES).count(),
            "approved_count": approved_queryset.count(),
            "dashboard_ready_count": dashboard_ready_count,
            "issue_count": total_issues,
            "critical_count": critical_count,
            "warning_count": warning_count,
            "info_count": info_count,
            "stale_after_days": stale_after_days,
        },
        "checks": [
            {
                "code": "application_review_queue",
                "status": "degraded" if any(issue.code in {"stale_trainer_application_review", "review_queue_incomplete_application"} for issue in issues) else "healthy",
                "description": "Submitted/under_review applications should be complete and not stuck indefinitely.",
            },
            {
                "code": "approved_access_sync",
                "status": "degraded" if any(issue.code.startswith("approved_without_") for issue in issues) else "healthy",
                "description": "Approved applications must grant trainer role and sync dashboard-ready profile layers.",
            },
            {
                "code": "profile_slug_integrity",
                "status": "degraded" if duplicate_profile_slugs else "healthy",
                "description": "Trainer public slugs must remain unique and routable.",
            },
            {
                "code": "review_audit_metadata",
                "status": "warning" if any(issue.code.endswith("without_reviewer_note") or issue.code.endswith("without_reviewed_at") for issue in issues) else "healthy",
                "description": "Reviewer notes and reviewed_at timestamps should explain all terminal decisions.",
            },
        ],
        "issues": issue_payloads,
        "api_surface": READINESS_API_SURFACE,
        "recommendations": recommendations if include_recommendations else [],
        "commands": [
            "python manage.py check_trainer_application_readiness --json",
            "python manage.py check_trainer_application_readiness --json --fail-on-degraded",
        ],
    }


def find_trainer_application_readiness_gaps(*, limit: int = 100) -> list[dict[str, Any]]:
    payload = build_trainer_application_readiness(limit=limit, include_samples=False, include_recommendations=False)
    return payload["issues"]
