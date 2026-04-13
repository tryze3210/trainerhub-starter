from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.access_control.api.serializers import (
    AccessSnapshotSerializer,
    FeatureCheckSerializer,
    FeatureDecisionSerializer,
    ObjectCheckSerializer,
    ObjectDecisionSerializer,
)
from apps.access_control.policies import PolicyService


class AccessSnapshotView(APIView):
    permission_classes = [IsAuthenticated]
    service = PolicyService()

    def get(self, request):
        payload = self.service.get_access_snapshot(user=request.user)
        return Response(AccessSnapshotSerializer(payload).data)


class FeatureCheckView(APIView):
    permission_classes = [IsAuthenticated]
    service = PolicyService()

    def post(self, request):
        serializer = FeatureCheckSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = self.service.require_feature(
            serializer.validated_data['feature_key'],
            capability=serializer.validated_data.get('capability') or None,
            user=request.user,
        )
        return Response(FeatureDecisionSerializer({
            'allowed': payload.allowed,
            'code': payload.code,
            'reason': payload.reason,
            'required_capability': payload.required_capability,
            'feature_key': payload.feature_key,
            'context': payload.context,
        }).data)


class ObjectCheckView(APIView):
    permission_classes = [IsAuthenticated]
    service = PolicyService()

    def post(self, request):
        serializer = ObjectCheckSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = self.service.require_object_access(
            serializer.validated_data['object_type'],
            serializer.validated_data['object_id'],
            serializer.validated_data['action'],
            user=request.user,
        )
        return Response(ObjectDecisionSerializer({
            'allowed': payload.allowed,
            'code': payload.code,
            'reason': payload.reason,
            'object_type': payload.object_type,
            'object_id': payload.object_id,
            'action': payload.action,
            'tenant_id': payload.tenant_id,
            'owner_account_id': payload.owner_account_id,
            'actor_account_id': payload.actor_account_id,
            'actor_role': payload.actor_role,
            'context': payload.context,
        }).data)
