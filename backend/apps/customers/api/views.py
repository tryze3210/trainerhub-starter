from rest_framework import permissions, response, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied

from apps.access_control.permissions import ROLE_ADMIN, ROLE_TRAINER, user_role_set
from apps.customers.models import CustomerNote, CustomerProfile, CustomerSegment
from apps.customers.selectors import CustomerMarketplaceHubSelector, TrainerCRMSelector


class CustomerMarketplaceHubViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]
    selector = CustomerMarketplaceHubSelector()

    def list(self, request):
        try:
            days = int(request.query_params.get("days", 30))
        except (TypeError, ValueError):
            days = 30
        return response.Response(self.selector.build(user=request.user, days=days), status=status.HTTP_200_OK)


class TrainerCRMNoteSerializer(serializers.Serializer):
    customer_id = serializers.UUIDField()
    body = serializers.CharField(max_length=4000)
    pinned = serializers.BooleanField(required=False, default=False)


class TrainerCRMSegmentSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=120)
    description = serializers.CharField(required=False, allow_blank=True, max_length=2000)
    color = serializers.CharField(required=False, allow_blank=True, max_length=24)


class TrainerCRMSegmentAssignSerializer(serializers.Serializer):
    customer_id = serializers.UUIDField()
    segment_id = serializers.UUIDField()


class TrainerCRMViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]
    selector = TrainerCRMSelector()

    def _require_trainer(self, request):
        roles = user_role_set(request.user)
        if request.user.is_staff or roles.intersection({ROLE_TRAINER, ROLE_ADMIN}):
            return
        raise PermissionDenied("Trainer CRM is available only for trainers.")

    def list(self, request):
        self._require_trainer(request)
        try:
            days = int(request.query_params.get("days", 90))
        except (TypeError, ValueError):
            days = 90
        try:
            limit = int(request.query_params.get("limit", 100))
        except (TypeError, ValueError):
            limit = 100
        payload = self.selector.build(
            trainer=request.user,
            days=days,
            limit=limit,
            search=request.query_params.get("search", ""),
        )
        return response.Response(payload, status=status.HTTP_200_OK)

    def retrieve(self, request, pk=None):
        self._require_trainer(request)
        try:
            payload = self.selector.detail(trainer=request.user, customer_id=pk)
        except PermissionError as exc:
            raise PermissionDenied(str(exc))
        return response.Response(payload, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"], url_path="notes")
    def create_note(self, request):
        self._require_trainer(request)
        serializer = TrainerCRMNoteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        customer_model = request.user.__class__
        customer = customer_model.objects.get(id=serializer.validated_data["customer_id"])
        if str(customer.id) not in self.selector._customer_ids_for_trainer(trainer=request.user):
            raise PermissionDenied("Customer is not connected to this trainer.")
        note = CustomerNote.objects.create(
            trainer=request.user,
            customer=customer,
            body=serializer.validated_data["body"].strip(),
            pinned=serializer.validated_data["pinned"],
        )
        return response.Response(
            {
                "id": str(note.id),
                "customer_id": str(customer.id),
                "body": note.body,
                "pinned": note.pinned,
                "visibility": note.visibility,
                "created_at": note.created_at.isoformat(),
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=["post"], url_path="segments")
    def create_segment(self, request):
        self._require_trainer(request)
        serializer = TrainerCRMSegmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        segment, _ = CustomerSegment.objects.get_or_create(
            trainer=request.user,
            name=serializer.validated_data["name"].strip(),
            defaults={
                "description": serializer.validated_data.get("description", "").strip(),
                "color": serializer.validated_data.get("color", "").strip(),
            },
        )
        return response.Response(
            {
                "id": str(segment.id),
                "name": segment.name,
                "description": segment.description,
                "color": segment.color,
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=["post"], url_path="segments/assign")
    def assign_segment(self, request):
        self._require_trainer(request)
        serializer = TrainerCRMSegmentAssignSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        customer_model = request.user.__class__
        customer = customer_model.objects.get(id=serializer.validated_data["customer_id"])
        if str(customer.id) not in self.selector._customer_ids_for_trainer(trainer=request.user):
            raise PermissionDenied("Customer is not connected to this trainer.")
        profile, _ = CustomerProfile.objects.get_or_create(user=customer, defaults={"display_name": customer.email})
        segment = CustomerSegment.objects.get(id=serializer.validated_data["segment_id"], trainer=request.user)
        segment.customers.add(profile)
        return response.Response({"assigned": True, "segment_id": str(segment.id), "customer_id": str(customer.id)})
