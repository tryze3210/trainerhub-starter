from __future__ import annotations

from typing import Any
from uuid import UUID

from django.shortcuts import get_object_or_404

from apps.content.models import PublishedLesson, PublishedProgram
from apps.entitlements.access_audit import AccessControlAuditService
from apps.trainer_cms.models import CourseLessonDraft, PublishStatus, TrainerCourseDraft


def _iso(value: Any) -> str | None:
    return value.isoformat() if value else None


def _uuid_or_none(value: Any) -> UUID | None:
    try:
        return UUID(str(value))
    except Exception:
        return None


def _is_staff(user) -> bool:
    return bool(user and user.is_authenticated and (getattr(user, "is_staff", False) or getattr(user, "is_superuser", False)))


def _program_owner_can_view(*, user, program: PublishedProgram) -> bool:
    if not user or not user.is_authenticated:
        return False
    profile = getattr(program, "trainer_profile", None)
    return bool(getattr(profile, "user_id", None) == user.id)


def _course_owner_can_view(*, user, course: TrainerCourseDraft) -> bool:
    if not user or not user.is_authenticated:
        return False
    profile = getattr(user, "trainer_public_profile", None)
    return bool(profile and str(profile.trainer_uuid) == str(course.trainer_id))


def _safe_decision(*, allowed: bool, code: str, reason: str, target_type: str, target_id: str) -> dict[str, Any]:
    return {
        "allowed": allowed,
        "code": code,
        "reason": reason,
        "target_type": target_type,
        "target_id": str(target_id),
        "entitlement_id": None,
        "source": None,
        "rules": [],
        "audit": {},
    }


def _published_lesson_payload(*, lesson: PublishedLesson, include_protected: bool) -> dict[str, Any]:
    return {
        "id": str(lesson.id),
        "lesson_id": str(lesson.source_draft_id),
        "slug": lesson.slug,
        "title": lesson.title,
        "description": lesson.description,
        "position": lesson.position,
        "duration_minutes": lesson.duration_minutes,
        "is_preview": lesson.is_preview,
        "video_asset_id": str(lesson.video_asset_id) if include_protected and lesson.video_asset_id else None,
        "materials": (lesson.materials or []) if include_protected else [],
        "created_at": _iso(lesson.created_at),
        "updated_at": _iso(lesson.updated_at),
    }


def _course_lesson_payload(*, lesson: CourseLessonDraft, include_protected: bool) -> dict[str, Any]:
    return {
        "id": str(lesson.id),
        "lesson_id": str(lesson.id),
        "title": lesson.title,
        "description": lesson.description,
        "position": lesson.position,
        "is_preview": lesson.is_preview,
        "video_asset_id": str(lesson.video_asset_id) if include_protected and lesson.video_asset_id else None,
        "materials": (lesson.materials or []) if include_protected else [],
        "created_at": _iso(lesson.created_at),
        "updated_at": _iso(lesson.updated_at),
    }


class ContentAccessRuntime:
    def open_program_lesson(self, *, user, program_slug: str, lesson_ref: str) -> tuple[int, dict[str, Any]]:
        program = get_object_or_404(
            PublishedProgram.objects.select_related("trainer_profile").prefetch_related("lessons"),
            slug=program_slug,
            is_active=True,
        )
        lesson_lookup = {"program": program}
        uuid_value = _uuid_or_none(lesson_ref)
        if uuid_value:
            lesson_lookup["source_draft_id"] = uuid_value
        elif str(lesson_ref).isdigit():
            lesson_lookup["id"] = int(str(lesson_ref))
        else:
            lesson_lookup["slug"] = str(lesson_ref)
        lesson = get_object_or_404(PublishedLesson, **lesson_lookup)

        is_preview = bool(lesson.is_preview)
        owner_allowed = _program_owner_can_view(user=user, program=program)
        admin_allowed = _is_staff(user)

        if is_preview:
            decision = _safe_decision(
                allowed=True,
                code="preview_lesson",
                reason="lesson_marked_preview",
                target_type="program",
                target_id=str(program.source_draft_id),
            )
        elif owner_allowed:
            decision = _safe_decision(
                allowed=True,
                code="trainer_owner",
                reason="trainer_owns_program",
                target_type="program",
                target_id=str(program.source_draft_id),
            )
        elif admin_allowed:
            decision = _safe_decision(
                allowed=True,
                code="admin_override",
                reason="staff_user_override",
                target_type="program",
                target_id=str(program.source_draft_id),
            )
        elif user and user.is_authenticated:
            decision = AccessControlAuditService.check(
                user=user,
                target_type="program",
                target_id=str(program.source_draft_id),
                include_admin_override=False,
            )
        else:
            decision = _safe_decision(
                allowed=False,
                code="authentication_required",
                reason="login_required_for_lesson",
                target_type="program",
                target_id=str(program.source_draft_id),
            )

        allowed = bool(decision.get("allowed"))
        payload = {
            "allowed": allowed,
            "blocked": not allowed,
            "runtime": "program_lesson",
            "program": {
                "id": str(program.id),
                "program_id": str(program.source_draft_id),
                "slug": program.slug,
                "title": program.title,
                "trainer_slug": program.trainer_profile.slug,
                "trainer_name": program.trainer_profile.display_name,
            },
            "lesson": _published_lesson_payload(lesson=lesson, include_protected=allowed),
            "access": decision,
        }
        return (200 if allowed else 403), payload

    def open_course_lesson(self, *, user, course_id: str, lesson_id: str) -> tuple[int, dict[str, Any]]:
        course = get_object_or_404(
            TrainerCourseDraft.objects.prefetch_related("lessons"),
            id=course_id,
            status=PublishStatus.PUBLISHED,
        )
        lesson = get_object_or_404(CourseLessonDraft, course_draft=course, id=lesson_id)

        is_preview = bool(lesson.is_preview)
        owner_allowed = _course_owner_can_view(user=user, course=course)
        admin_allowed = _is_staff(user)

        if is_preview:
            decision = _safe_decision(
                allowed=True,
                code="preview_lesson",
                reason="lesson_marked_preview",
                target_type="course",
                target_id=str(course.id),
            )
        elif owner_allowed:
            decision = _safe_decision(
                allowed=True,
                code="trainer_owner",
                reason="trainer_owns_course",
                target_type="course",
                target_id=str(course.id),
            )
        elif admin_allowed:
            decision = _safe_decision(
                allowed=True,
                code="admin_override",
                reason="staff_user_override",
                target_type="course",
                target_id=str(course.id),
            )
        elif user and user.is_authenticated:
            decision = AccessControlAuditService.check(
                user=user,
                target_type="course",
                target_id=str(course.id),
                include_admin_override=False,
            )
        else:
            decision = _safe_decision(
                allowed=False,
                code="authentication_required",
                reason="login_required_for_lesson",
                target_type="course",
                target_id=str(course.id),
            )

        allowed = bool(decision.get("allowed"))
        payload = {
            "allowed": allowed,
            "blocked": not allowed,
            "runtime": "course_lesson",
            "course": {
                "id": str(course.id),
                "course_id": str(course.id),
                "slug": course.slug,
                "title": course.title,
                "metadata": course.metadata or {},
            },
            "lesson": _course_lesson_payload(lesson=lesson, include_protected=allowed),
            "access": decision,
        }
        return (200 if allowed else 403), payload
