from django.db.models import Sum

from apps.progress.models import LessonProgress, ProgramProgress, VideoProgress


def _mask_student_email(email: str) -> str:
    email = str(email or '').strip()
    if '@' not in email:
        return ''
    local, domain = email.split('@', 1)
    if not local or not domain:
        return ''
    visible = local[:1]
    return f'{visible}***@{domain}'


def _can_view_student_email(user) -> bool:
    return bool(getattr(user, 'is_staff', False) or getattr(user, 'is_superuser', False))


def get_video_progress_for_user(*, user):
    return VideoProgress.objects.filter(user=user).order_by('-updated_at')



def get_lesson_progress_for_user(*, user):
    return LessonProgress.objects.filter(user=user).order_by('-updated_at')



def get_program_progress_for_user(*, user):
    return ProgramProgress.objects.filter(user=user).order_by('-updated_at')



def get_progress_summary(*, user):
    video_qs = get_video_progress_for_user(user=user)
    lesson_qs = get_lesson_progress_for_user(user=user)
    program_qs = get_program_progress_for_user(user=user)
    watched_seconds = video_qs.aggregate(total=Sum('watched_seconds')).get('total') or 0
    return {
        'watched_seconds': watched_seconds,
        'completed_videos': video_qs.filter(is_completed=True).count(),
        'completed_lessons': lesson_qs.filter(is_completed=True).count(),
        'completed_programs': program_qs.filter(is_completed=True).count(),
        'active_programs': program_qs.count(),
    }


def get_trainer_student_progress(*, trainer_user):
    from apps.content.models import PublishedProgram
    from apps.trainer_cms.models import TrainerCourseDraft

    public_profile = getattr(trainer_user, 'trainer_public_profile', None)
    trainer_uuid = getattr(public_profile, 'trainer_uuid', None)

    program_ids = list(
        PublishedProgram.objects.filter(trainer_profile__user=trainer_user)
        .values_list('source_draft_id', flat=True)
    )
    course_ids = list(TrainerCourseDraft.objects.filter(trainer_id=trainer_uuid).values_list('id', flat=True)) if trainer_uuid else []

    rows = ProgramProgress.objects.filter(
        content_type=ProgramProgress.ContentType.PROGRAM,
        program_id__in=[str(value) for value in program_ids],
    ) | ProgramProgress.objects.filter(
        content_type=ProgramProgress.ContentType.COURSE,
        program_id__in=[str(value) for value in course_ids],
    )
    students_count = rows.values('user_id').distinct().count()
    records_count = rows.count()
    completed_count = rows.filter(is_completed=True).count()
    page = rows.select_related('user').order_by('-last_activity_at', '-updated_at')[:200]
    can_view_student_email = _can_view_student_email(trainer_user)

    return {
        'summary': {
            'students_count': students_count,
            'records_count': records_count,
            'completed_count': completed_count,
        },
        'items': [
            {
                'student_id': str(row.user_id),
                'student_email': (
                    getattr(row.user, 'email', '')
                    if can_view_student_email
                    else _mask_student_email(getattr(row.user, 'email', ''))
                ),
                'student_email_masked': not can_view_student_email,
                'content_type': row.content_type,
                'program_id': row.program_id,
                'total_lessons': row.total_lessons,
                'completed_lessons': row.completed_lessons,
                'completion_percent': str(row.completion_percent),
                'is_completed': row.is_completed,
                'last_activity_at': row.last_activity_at.isoformat() if row.last_activity_at else None,
                'updated_at': row.updated_at.isoformat() if row.updated_at else None,
            }
            for row in page
        ],
    }
