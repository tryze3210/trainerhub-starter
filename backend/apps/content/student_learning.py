from __future__ import annotations

from typing import Any
from uuid import UUID

from django.db.models import Q
from django.utils import timezone

from apps.content.models import PublishedProgram, PublishedVideo
from apps.entitlements.access_audit import AccessControlAuditService
from apps.entitlements.models import Entitlement, EntitlementStatus, EntitlementTargetType
from apps.progress.models import LessonProgress, ProgramProgress
from apps.trainer_cms.models import PublishStatus, TrainerCourseDraft


def _iso(value: Any) -> str | None:
    return value.isoformat() if value else None


def _uuid_or_none(value: Any) -> UUID | None:
    try:
        return UUID(str(value))
    except Exception:
        return None


def _active_entitlements(user):
    now = timezone.now()
    return (
        Entitlement.objects.filter(user=user, status=EntitlementStatus.ACTIVE)
        .filter(Q(starts_at__isnull=True) | Q(starts_at__lte=now))
        .filter(Q(ends_at__isnull=True) | Q(ends_at__gte=now))
        .select_related("source_order", "source_subscription")
        .order_by("-created_at")
    )


def _program_lookup(target_id: str):
    lookup = Q(slug=target_id)
    uuid_value = _uuid_or_none(target_id)
    if uuid_value:
        lookup = lookup | Q(source_draft_id=uuid_value)
    if str(target_id).isdigit():
        lookup = lookup | Q(id=int(str(target_id)))
    return (
        PublishedProgram.objects.select_related("trainer_profile")
        .prefetch_related("lessons")
        .filter(lookup, is_active=True)
        .first()
    )


def _video_lookup(target_id: str):
    lookup = Q(slug=target_id)
    uuid_value = _uuid_or_none(target_id)
    if uuid_value:
        lookup = lookup | Q(source_draft_id=uuid_value)
    if str(target_id).isdigit():
        lookup = lookup | Q(id=int(str(target_id)))
    return PublishedVideo.objects.select_related("trainer_profile").filter(lookup, is_active=True).first()


def _course_lookup(target_id: str):
    uuid_value = _uuid_or_none(target_id)
    if not uuid_value:
        return None
    return (
        TrainerCourseDraft.objects.prefetch_related("lessons")
        .filter(id=uuid_value, status=PublishStatus.PUBLISHED)
        .first()
    )


def _progress_maps(*, user, content_type: str, program_id: str):
    program_progress = ProgramProgress.objects.filter(
        user=user,
        content_type=content_type,
        program_id=program_id,
    ).first()
    lessons = {
        row.lesson_id: row
        for row in LessonProgress.objects.filter(
            user=user,
            content_type=content_type,
            program_id=program_id,
        )
    }
    return program_progress, lessons


def _program_item(*, user, program: PublishedProgram, entitlement: Entitlement, access: dict[str, Any]) -> dict[str, Any]:
    program_id = str(program.source_draft_id)
    program_progress, lesson_progress = _progress_maps(
        user=user,
        content_type=ProgramProgress.ContentType.PROGRAM,
        program_id=program_id,
    )
    lessons = []
    materials = []
    for lesson in program.lessons.all().order_by("position", "created_at"):
        lesson_materials = lesson.materials or []
        runtime_url = f"/content/runtime/programs/{program.slug}/lessons/{lesson.slug}/"
        lessons.append(
            {
                "id": str(lesson.id),
                "lesson_id": str(lesson.source_draft_id),
                "program_id": program_id,
                "content_type": "program",
                "title": lesson.title,
                "description": lesson.description,
                "position": lesson.position,
                "is_preview": lesson.is_preview,
                "duration_minutes": lesson.duration_minutes,
                "materials_count": len(lesson_materials),
                "runtime_url": runtime_url,
                "is_completed": bool(lesson_progress.get(str(lesson.source_draft_id)) and lesson_progress[str(lesson.source_draft_id)].is_completed),
                "completed_at": _iso(lesson_progress[str(lesson.source_draft_id)].completed_at) if lesson_progress.get(str(lesson.source_draft_id)) else None,
            }
        )
        for material in lesson_materials:
            materials.append({**material, "lesson_id": str(lesson.source_draft_id), "lesson_title": lesson.title})
    return {
        "id": str(program.id),
        "kind": "program",
        "target_id": str(program.source_draft_id),
        "title": program.title,
        "slug": program.slug,
        "description": program.description,
        "trainer_name": program.trainer_profile.display_name,
        "trainer_slug": program.trainer_profile.slug,
        "status": "available",
        "progress_percent": str(program_progress.completion_percent) if program_progress else "0.00",
        "last_activity_at": _iso(program_progress.last_activity_at) if program_progress else None,
        "entitlement_id": str(entitlement.id),
        "access": access,
        "lessons": lessons,
        "materials": materials,
        "created_at": _iso(program.created_at),
    }


def _course_item(*, user, course: TrainerCourseDraft, entitlement: Entitlement, access: dict[str, Any]) -> dict[str, Any]:
    course_id = str(course.id)
    course_progress, lesson_progress = _progress_maps(
        user=user,
        content_type=ProgramProgress.ContentType.COURSE,
        program_id=course_id,
    )
    lessons = []
    materials = []
    for lesson in course.lessons.all().order_by("position", "created_at"):
        lesson_materials = lesson.materials or []
        runtime_url = f"/content/runtime/courses/{course.id}/lessons/{lesson.id}/"
        lessons.append(
            {
                "id": str(lesson.id),
                "lesson_id": str(lesson.id),
                "program_id": course_id,
                "content_type": "course",
                "title": lesson.title,
                "description": lesson.description,
                "position": lesson.position,
                "is_preview": lesson.is_preview,
                "duration_minutes": 0,
                "materials_count": len(lesson_materials),
                "runtime_url": runtime_url,
                "is_completed": bool(lesson_progress.get(str(lesson.id)) and lesson_progress[str(lesson.id)].is_completed),
                "completed_at": _iso(lesson_progress[str(lesson.id)].completed_at) if lesson_progress.get(str(lesson.id)) else None,
            }
        )
        for material in lesson_materials:
            materials.append({**material, "lesson_id": str(lesson.id), "lesson_title": lesson.title})
    return {
        "id": str(course.id),
        "kind": "course",
        "target_id": str(course.id),
        "title": course.title,
        "slug": course.slug,
        "description": course.description,
        "trainer_name": "",
        "trainer_slug": "",
        "status": "available",
        "progress_percent": str(course_progress.completion_percent) if course_progress else "0.00",
        "last_activity_at": _iso(course_progress.last_activity_at) if course_progress else None,
        "entitlement_id": str(entitlement.id),
        "access": access,
        "lessons": lessons,
        "materials": materials,
        "created_at": _iso(course.created_at),
    }


def _video_item(*, video: PublishedVideo, entitlement: Entitlement, access: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(video.id),
        "kind": "video",
        "target_id": str(video.source_draft_id),
        "title": video.title,
        "slug": video.slug,
        "description": video.description,
        "trainer_name": video.trainer_profile.display_name,
        "trainer_slug": video.trainer_profile.slug,
        "status": "available",
        "progress_percent": 0,
        "last_activity_at": None,
        "entitlement_id": str(entitlement.id),
        "access": access,
        "lessons": [],
        "materials": [],
        "access_url": f"/catalog/videos/{video.slug}",
        "created_at": _iso(video.created_at),
    }


class StudentLearningAreaSelector:
    def build(self, *, user) -> dict[str, Any]:
        items: list[dict[str, Any]] = []
        unresolved: list[dict[str, Any]] = []
        library_access = False

        for entitlement in _active_entitlements(user):
            target_type = entitlement.target_type
            target_id = str(entitlement.target_id or "")
            if target_type == EntitlementTargetType.LIBRARY:
                access = AccessControlAuditService.check(user=user, target_type="video", target_id="library", include_admin_override=False)
                library_access = bool(access.get("allowed"))
                continue

            access = AccessControlAuditService.check(
                user=user,
                target_type=target_type,
                target_id=target_id,
                include_admin_override=False,
            )
            if not access.get("allowed"):
                unresolved.append(
                    {
                        "entitlement_id": str(entitlement.id),
                        "target_type": target_type,
                        "target_id": target_id,
                        "reason": access.get("code"),
                    }
                )
                continue

            if target_type == EntitlementTargetType.PROGRAM:
                program = _program_lookup(target_id)
                if program:
                    items.append(_program_item(user=user, program=program, entitlement=entitlement, access=access))
                    continue
            elif target_type == EntitlementTargetType.COURSE or target_type == "course":
                course = _course_lookup(target_id)
                if course:
                    items.append(_course_item(user=user, course=course, entitlement=entitlement, access=access))
                    continue
            elif target_type == EntitlementTargetType.VIDEO:
                video = _video_lookup(target_id)
                if video:
                    items.append(_video_item(video=video, entitlement=entitlement, access=access))
                    continue

            unresolved.append(
                {
                    "entitlement_id": str(entitlement.id),
                    "target_type": target_type,
                    "target_id": target_id,
                    "reason": "content_not_resolved",
                }
            )

        lessons_count = sum(len(item.get("lessons") or []) for item in items)
        materials_count = sum(len(item.get("materials") or []) for item in items)
        next_lesson = next(
            (
                lesson
                for item in items
                for lesson in item.get("lessons", [])
                if lesson and not lesson.get("is_completed")
            ),
            None,
        )

        return {
            "summary": {
                "items_count": len(items),
                "courses_count": len([item for item in items if item["kind"] == "course"]),
                "programs_count": len([item for item in items if item["kind"] == "program"]),
                "videos_count": len([item for item in items if item["kind"] == "video"]),
                "lessons_count": lessons_count,
                "materials_count": materials_count,
                "library_access": library_access,
                "unresolved_count": len(unresolved),
            },
            "items": items,
            "next_lesson": next_lesson,
            "materials": [material for item in items for material in item.get("materials", [])],
            "unresolved": unresolved,
        }
