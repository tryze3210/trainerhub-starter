from django.urls import path
from .views import (
    MyHabitPlansView,
    MyHabitDashboardView,
    SubmitDailyCheckInView,
    MyJournalView,
    AdminHabitOverviewView,
)

urlpatterns = [
    path("me/plans/", MyHabitPlansView.as_view()),
    path("me/dashboard/", MyHabitDashboardView.as_view()),
    path("me/checkins/", SubmitDailyCheckInView.as_view()),
    path("me/journal/", MyJournalView.as_view()),
    path("admin/overview/", AdminHabitOverviewView.as_view()),
]
