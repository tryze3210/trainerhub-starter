from rest_framework import generics, permissions, response, status, views

from apps.disputes.api.serializers import CreateDisputeCaseSerializer, DisputeCaseSerializer, RefundReviewSerializer
from apps.disputes.models import DisputeCase
from apps.disputes.services.case_service import CreateDisputeCaseDTO, DisputeCaseService
from apps.disputes.services.refund_service import RefundReviewService
from apps.disputes.services.selectors import DisputeSelectors


class AdminOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)


class MyDisputeListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = DisputeCaseSerializer

    def get_queryset(self):
        return DisputeCase.objects.filter(opened_by=self.request.user).prefetch_related("events")

    def create(self, request, *args, **kwargs):
        serializer = CreateDisputeCaseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        dto = CreateDisputeCaseDTO(opened_by_id=request.user.id, **serializer.validated_data)
        case = DisputeCaseService.create_case(dto)
        return response.Response(DisputeCaseSerializer(case).data, status=status.HTTP_201_CREATED)


class MyDisputeDetailView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = DisputeCaseSerializer
    lookup_field = "id"

    def get_queryset(self):
        return DisputeCase.objects.filter(opened_by=self.request.user).prefetch_related("events")


class AdminDisputeOverviewView(views.APIView):
    permission_classes = [AdminOnly]

    def get(self, request):
        return response.Response(DisputeSelectors.admin_overview())


class AdminDisputeQueueView(generics.ListAPIView):
    permission_classes = [AdminOnly]
    serializer_class = DisputeCaseSerializer

    def get_queryset(self):
        filters = {
            "status": self.request.query_params.get("status"),
            "dispute_type": self.request.query_params.get("dispute_type"),
            "trainer_id": self.request.query_params.get("trainer_id"),
        }
        return DisputeSelectors.queue(filters).prefetch_related("events")


class AdminDisputeDecisionView(views.APIView):
    permission_classes = [AdminOnly]

    def post(self, request, id):
        case = DisputeCase.objects.get(id=id)
        new_status = request.data.get("status", DisputeCase.STATUS_UNDER_REVIEW)
        note = request.data.get("note", "")
        DisputeCaseService.set_status(case, actor_id=request.user.id, status=new_status, note=note)
        return response.Response(DisputeCaseSerializer(case).data)


class AdminRefundReviewView(views.APIView):
    permission_classes = [AdminOnly]

    def post(self, request, id):
        case = DisputeCase.objects.select_related("refund_review").get(id=id)
        refund_review = RefundReviewService.review(
            case.refund_review,
            reviewed_by_id=request.user.id,
            decision=request.data.get("decision", "rejected"),
            approved_amount=request.data.get("approved_amount", "0.00"),
            rationale=request.data.get("rationale", ""),
        )
        return response.Response(RefundReviewSerializer(refund_review).data)
