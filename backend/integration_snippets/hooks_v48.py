"""
Integration seam.
Call these from application services in habits/cohorts/live_sessions.
Do not call directly from model save() or generic signals.
"""

from apps.gamification.services.awarding import AchievementAwardingService


def on_daily_checkin_completed(*, user, checkin_id: str):
    return AchievementAwardingService().award_for_event(
        user=user,
        event_type='daily_checkin_completed',
        source_event_id=str(checkin_id),
    )


def on_habit_streak_milestone(*, user, streak_id: str, streak_days: int):
    return AchievementAwardingService().award_for_event(
        user=user,
        event_type='habit_streak_milestone',
        source_event_id=str(streak_id),
        metadata={'streak_days': streak_days},
    )


def on_cohort_checkpoint_completed(*, user, progress_id: str, cohort_id: str):
    return AchievementAwardingService().award_for_event(
        user=user,
        event_type='cohort_checkpoint_completed',
        source_event_id=str(progress_id),
        metadata={'cohort_id': cohort_id},
    )


def on_live_session_attended(*, user, attendance_id: str, live_session_id: str):
    return AchievementAwardingService().award_for_event(
        user=user,
        event_type='live_session_attended',
        source_event_id=str(attendance_id),
        metadata={'live_session_id': live_session_id},
    )
