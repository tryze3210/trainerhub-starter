from rest_framework.response import Response
from rest_framework.views import APIView

from apps.trainer_profiles import selectors, services
from apps.trainer_profiles.api.serializers import PublicTrainerDetailSerializer, PublicTrainerSerializer


class PublicTrainerListView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        data = selectors.list_public_trainers()
        return Response(PublicTrainerSerializer(data, many=True).data)


class PublicTrainerDetailView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, slug: str):
        trainer = services.build_public_trainer_profile(slug)
        return Response(PublicTrainerDetailSerializer(trainer).data)
