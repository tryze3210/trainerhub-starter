from django.urls import path

from apps.onboarding.api.views import OnboardingCompleteStepView, OnboardingStatusView, OnboardingStepsView

urlpatterns = [
    path("steps/", OnboardingStepsView.as_view(), name="onboarding-steps"),
    path("complete-step/", OnboardingCompleteStepView.as_view(), name="onboarding-complete-step"),
    path("status/", OnboardingStatusView.as_view(), name="onboarding-status"),
]
