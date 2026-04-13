from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.ops.api.serializers import DiagnosticsSnapshotSerializer, DiagnosticsRunSerializer, RunDiagnosticsSerializer
from apps.ops.services import DiagnosticsService


class DiagnosticsSnapshotView(APIView):
    service = DiagnosticsService()

    def get(self, request):
        return Response(DiagnosticsSnapshotSerializer(self.service.snapshot()).data)


class RunDiagnosticsView(APIView):
    service = DiagnosticsService()

    def post(self, request):
        serializer = RunDiagnosticsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = self.service.run(**serializer.validated_data)
        return Response({'run': DiagnosticsRunSerializer(payload['run']).data, 'status': payload['status']}, status=status.HTTP_202_ACCEPTED)
