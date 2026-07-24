from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.projections.api.serializers import ProjectionRebuildSerializer, ProjectionStatusSerializer
from apps.projections.services import ProjectionService


class ProjectionStatusListView(APIView):
    permission_classes = [permissions.IsAdminUser]
    service = ProjectionService()

    def get(self, request):
        return Response(ProjectionStatusSerializer(self.service.list_statuses(), many=True).data)


class ProjectionRebuildView(APIView):
    permission_classes = [permissions.IsAdminUser]
    service = ProjectionService()

    def post(self, request):
        serializer = ProjectionRebuildSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = self.service.rebuild(serializer.validated_data['projection_key'])
        return Response(payload, status=status.HTTP_202_ACCEPTED)
