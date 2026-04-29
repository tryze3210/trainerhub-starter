from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.trainers.api.serializers import (
    TrainerApplicationSerializer,
    TrainerApplicationUpsertSerializer,
    TrainerProfileSerializer,
)
from apps.trainers.models import TrainerProfile
from apps.trainers.selectors.trainer_catalog import get_public_trainer_catalog_queryset
from apps.trainers.services.applications import TrainerApplicationService
from apps.trainers.services.create_profile import CreateTrainerProfileService
from common.permissions import IsTrainer


class TrainerCatalogApi(generics.ListAPIView):
    serializer_class = TrainerProfileSerializer
    queryset = TrainerProfile.objects.none()
    search_fields = ('display_name', 'headline', 'bio')
    ordering_fields = ('created_at', 'views_count', 'sales_count', 'rating_avg')

    def get_queryset(self):
        return get_public_trainer_catalog_queryset()


class TrainerDetailApi(generics.RetrieveAPIView):
    serializer_class = TrainerProfileSerializer
    lookup_field = 'slug'
    queryset = TrainerProfile.objects.filter(is_public=True, is_deleted=False)


class TrainerApplicationApi(APIView):
    permission_classes = [permissions.IsAuthenticated]
    service = TrainerApplicationService()

    def get(self, request):
        application = self.service.get_application(user=request.user)
        return Response(TrainerApplicationSerializer(application).data)

    def patch(self, request):
        serializer = TrainerApplicationUpsertSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        application = self.service.upsert_application(user=request.user, payload=serializer.validated_data)
        return Response(TrainerApplicationSerializer(application).data)


class TrainerApplicationSubmitApi(APIView):
    permission_classes = [permissions.IsAuthenticated]
    service = TrainerApplicationService()

    def post(self, request):
        serializer = TrainerApplicationUpsertSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        application = self.service.submit_application(user=request.user, payload=serializer.validated_data)
        return Response(TrainerApplicationSerializer(application).data, status=status.HTTP_202_ACCEPTED)


class TrainerMeProfileApi(APIView):
    permission_classes = [permissions.IsAuthenticated, IsTrainer]

    def get_object(self, request):
        return getattr(request.user, 'trainer_profile', None)

    def get(self, request):
        profile = self.get_object(request)
        if not profile:
            return Response({'detail': 'Trainer profile not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(TrainerProfileSerializer(profile).data)

    def post(self, request):
        if self.get_object(request):
            return Response({'detail': 'Trainer profile already exists.'}, status=status.HTTP_400_BAD_REQUEST)
        serializer = TrainerProfileSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        profile = CreateTrainerProfileService().execute(user=request.user, **serializer.validated_data)
        return Response(TrainerProfileSerializer(profile).data, status=status.HTTP_201_CREATED)

    def patch(self, request):
        profile = self.get_object(request)
        if not profile:
            return Response({'detail': 'Trainer profile not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = TrainerProfileSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
