from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from apps.audit.services import AuditService
from apps.content.models import PublishedLesson, PublishedProgram
from apps.content.selectors import get_lesson_detail, get_program_detail, get_video_detail, user_has_lesson_access, user_has_video_access
from apps.entitlements.access_audit import AccessControlAuditService
from apps.progress.models import LessonProgress, ProgramProgress, VideoProgress
from apps.trainer_cms.models import CourseLessonDraft, TrainerCourseDraft


def _resolve_lesson_context(*, user, lesson_id: str, content_type: str = '', program_id: str = '') -> dict:
    content_type = content_type or ''
    if content_type == LessonProgress.ContentType.COURSE or (content_type == 'course'):
        lesson = CourseLessonDraft.objects.select_related('course_draft').filter(id=lesson_id).first()
        if lesson is None:
            raise ValueError('Course lesson not found')
        course = lesson.course_draft
        return {
            'content_type': LessonProgress.ContentType.COURSE,
            'program_id': str(program_id or course.id),
            'lesson_id': str(lesson.id),
            'total_lessons': course.lessons.count(),
            'access': AccessControlAuditService.check(
                user=user,
                target_type='course',
                target_id=str(course.id),
                include_admin_override=False,
            ),
        }

    published_lesson = PublishedLesson.objects.select_related('program').filter(source_draft_id=lesson_id).first()
    if published_lesson is None:
        published_lesson = PublishedLesson.objects.select_related('program').filter(id=lesson_id).first() if str(lesson_id).isdigit() else None
    if published_lesson is not None:
        program = published_lesson.program
        return {
            'content_type': LessonProgress.ContentType.PROGRAM,
            'program_id': str(program_id or program.source_draft_id),
            'lesson_id': str(published_lesson.source_draft_id),
            'total_lessons': program.lessons.count(),
            'access': AccessControlAuditService.check(
                user=user,
                target_type='program',
                target_id=str(program.source_draft_id),
                include_admin_override=False,
            ),
        }

    lesson = get_lesson_detail(lesson_id=lesson_id, user=user)
    return {
        'content_type': LessonProgress.ContentType.PROGRAM,
        'program_id': str(program_id or lesson['program_id']),
        'lesson_id': str(lesson_id),
        'total_lessons': len(get_program_detail(program_id=lesson['program_id']).get('lesson_ids') or []),
        'access': {'allowed': user_has_lesson_access(user=user, lesson_id=lesson_id)},
    }


class ProgressService:
    @classmethod
    @transaction.atomic
    def save_video_progress(cls, *, user, video_id: str, watched_seconds: int, last_position_seconds: int, request=None):
        if not user_has_video_access(user=user, video_id=video_id):
            raise PermissionError('No video entitlement')
        video = get_video_detail(video_id=video_id)
        duration_seconds = max(video['duration_seconds'], 1)
        watched_seconds = min(max(watched_seconds, 0), duration_seconds)
        completion_percent = Decimal(watched_seconds * 100 / duration_seconds).quantize(Decimal('0.01'))
        is_completed = watched_seconds >= int(duration_seconds * 0.9)
        obj, _ = VideoProgress.objects.update_or_create(
            user=user,
            video_id=video_id,
            defaults={
                'watched_seconds': watched_seconds,
                'last_position_seconds': min(max(last_position_seconds, 0), duration_seconds),
                'duration_seconds': duration_seconds,
                'completion_percent': completion_percent,
                'is_completed': is_completed,
                'last_watched_at': timezone.now(),
            },
        )
        AuditService.log(actor=user, event_type='video.progress.saved', entity_type='video', entity_id=video_id, context={'watched_seconds': watched_seconds}, request=request)
        return obj

    @classmethod
    @transaction.atomic
    def mark_lesson_completed(cls, *, user, lesson_id: str, program_id: str = '', content_type: str = '', request=None):
        context = _resolve_lesson_context(user=user, lesson_id=lesson_id, content_type=content_type, program_id=program_id)
        if not context['access'].get('allowed'):
            raise PermissionError('No lesson entitlement')
        obj, _ = LessonProgress.objects.update_or_create(
            user=user,
            lesson_id=context['lesson_id'],
            defaults={
                'program_id': context['program_id'],
                'content_type': context['content_type'],
                'is_completed': True,
                'completed_at': timezone.now(),
            },
        )
        cls.recalculate_program_progress(user=user, program_id=context['program_id'], content_type=context['content_type'], total_lessons=context['total_lessons'])
        AuditService.log(
            actor=user,
            event_type='lesson.completed',
            entity_type='lesson',
            entity_id=context['lesson_id'],
            context={'program_id': context['program_id'], 'content_type': context['content_type']},
            request=request,
        )
        return obj

    @classmethod
    @transaction.atomic
    def recalculate_program_progress(cls, *, user, program_id: str, content_type: str = LessonProgress.ContentType.PROGRAM, total_lessons: int | None = None):
        if total_lessons is None:
            if content_type == LessonProgress.ContentType.COURSE or content_type == 'course':
                course = TrainerCourseDraft.objects.filter(id=program_id).first()
                total_lessons = course.lessons.count() if course else 0
            else:
                program = get_program_detail(program_id=program_id)
                total_lessons = len(program['lesson_ids'])
        completed_lessons = LessonProgress.objects.filter(
            user=user,
            content_type=content_type,
            program_id=program_id,
            is_completed=True,
        ).count()
        completion_percent = Decimal((completed_lessons * 100 / total_lessons) if total_lessons else 0).quantize(Decimal('0.01'))
        is_completed = total_lessons > 0 and completed_lessons >= total_lessons
        now = timezone.now()
        obj, _ = ProgramProgress.objects.update_or_create(
            user=user,
            program_id=program_id,
            defaults={
                'content_type': content_type,
                'total_lessons': total_lessons,
                'completed_lessons': completed_lessons,
                'completion_percent': completion_percent,
                'is_completed': is_completed,
                'completed_at': now if is_completed else None,
                'last_activity_at': now,
            },
        )
        return obj
