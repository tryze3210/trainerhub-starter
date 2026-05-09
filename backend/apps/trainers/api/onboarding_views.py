from __future__ import annotations

from django.shortcuts import get_object_or_404

from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.trainers.api.onboarding_serializers import (
    AdminTrainerApplicationListQuerySerializer,
    AdminTrainerApplicationReviewSerializer,
    TrainerOnboardingStateQuerySerializer,
)
from apps.trainers.onboarding_flow import (
    get_trainer_onboarding_state,
    list_trainer_applications,
    review_trainer_application,
    serialize_admin_application,
    sync_approved_trainer_access,
)
from apps.trainers.models import TrainerApplication


class TrainerOnboardingStateApi(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = TrainerOnboardingStateQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        return Response(get_trainer_onboarding_state(user=request.user))


class TrainerApplicationStatusApi(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        state = get_trainer_onboarding_state(user=request.user)
        return Response(
            {
                "application": state["application"],
                "profile": state["profile"],
                "dashboard_unlocked": state["dashboard_unlocked"],
                "can_access_content_studio": state["can_access_content_studio"],
                "summary": state["summary"],
                "steps": state["steps"],
            }
        )


class AdminTrainerApplicationListApi(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        serializer = AdminTrainerApplicationListQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        payload = list_trainer_applications(
            status_filter=serializer.validated_data.get("status") or None,
            search=serializer.validated_data.get("search") or None,
            limit=serializer.validated_data["limit"],
        )
        return Response(payload)


class AdminTrainerApplicationDetailApi(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request, application_id):
        application = get_object_or_404(TrainerApplication.objects.select_related("user"), id=application_id)
        return Response(serialize_admin_application(application))


class AdminTrainerApplicationReviewApi(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, application_id):
        serializer = AdminTrainerApplicationReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = review_trainer_application(
            application_id=str(application_id),
            decision=serializer.validated_data["decision"],
            reviewer_note=serializer.validated_data.get("reviewer_note", ""),
            reviewer=request.user,
        )
        return Response(payload, status=status.HTTP_200_OK)


class AdminTrainerApplicationSyncAccessApi(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, application_id):
        payload = sync_approved_trainer_access(application_id=str(application_id))
        return Response(payload, status=status.HTTP_200_OK)
