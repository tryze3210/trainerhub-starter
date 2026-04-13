from rest_framework.response import Response
from rest_framework.views import APIView

from apps.reviews import services
from apps.reviews.api.serializers import TargetReviewPayloadSerializer


class TargetReviewsView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, target_type: str, target_id: str):
        payload = services.build_target_reviews(target_type, target_id)
        return Response(TargetReviewPayloadSerializer(payload).data)
