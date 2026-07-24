from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.workflows.api.serializers import StartWorkflowSerializer, WorkflowDefinitionSerializer, WorkflowRunSerializer
from apps.workflows.services import WorkflowService


class WorkflowDefinitionListView(APIView):
    permission_classes = [permissions.IsAdminUser]
    service = WorkflowService()

    def get(self, request):
        return Response(WorkflowDefinitionSerializer(self.service.list_definitions(), many=True).data)


class WorkflowRunListView(APIView):
    permission_classes = [permissions.IsAdminUser]
    service = WorkflowService()

    def get(self, request):
        return Response(WorkflowRunSerializer(self.service.list_runs(), many=True).data)


class WorkflowStartView(APIView):
    permission_classes = [permissions.IsAdminUser]
    service = WorkflowService()

    def post(self, request):
        serializer = StartWorkflowSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = self.service.start(**serializer.validated_data)
        return Response(payload, status=status.HTTP_202_ACCEPTED)
