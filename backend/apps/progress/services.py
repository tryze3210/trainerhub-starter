from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from apps.audit.services import AuditService
from apps.content.selectors import get_lesson_detail, get_program_detail, get_video_detail, user_has_lesson_access, user_has_video_access
from apps.progress.models import LessonProgress, ProgramProgress, VideoProgress


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
    def mark_lesson_completed(cls, *, user, lesson_id: str, request=None):
        if not user_has_lesson_access(user=user, lesson_id=lesson_id):
            raise PermissionError('No lesson entitlement')
        lesson = get_lesson_detail(lesson_id=lesson_id)
        obj, _ = LessonProgress.objects.update_or_create(
            user=user,
            lesson_id=lesson_id,
            defaults={
                'program_id': lesson['program_id'],
                'is_completed': True,
                'completed_at': timezone.now(),
            },
        )
        cls.recalculate_program_progress(user=user, program_id=lesson['program_id'])
        AuditService.log(actor=user, event_type='lesson.completed', entity_type='lesson', entity_id=lesson_id, context={'program_id': lesson['program_id']}, request=request)
        return obj

    @classmethod
    @transaction.atomic
    def recalculate_program_progress(cls, *, user, program_id: str):
        program = get_program_detail(program_id=program_id)
        total_lessons = len(program['lesson_ids'])
        completed_lessons = LessonProgress.objects.filter(user=user, program_id=program_id, is_completed=True).count()
        completion_percent = Decimal((completed_lessons * 100 / total_lessons) if total_lessons else 0).quantize(Decimal('0.01'))
        is_completed = total_lessons > 0 and completed_lessons >= total_lessons
        obj, _ = ProgramProgress.objects.update_or_create(
            user=user,
            program_id=program_id,
            defaults={
                'total_lessons': total_lessons,
                'completed_lessons': completed_lessons,
                'completion_percent': completion_percent,
                'is_completed': is_completed,
                'completed_at': timezone.now() if is_completed else None,
            },
        )
        return obj
