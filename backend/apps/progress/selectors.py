from django.db.models import Sum

from apps.progress.models import LessonProgress, ProgramProgress, VideoProgress



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
