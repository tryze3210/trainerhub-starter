from rest_framework import permissions, response, status, views
from rest_framework.exceptions import NotFound

from apps.reviews import selectors
from apps.reviews.api.serializers import (
    ReviewCreateSerializer,
    ReviewModerationSerializer,
    ReviewReplySerializer,
    ReviewSerializer,
    TargetReviewPayloadSerializer,
)
from apps.reviews.models import Review
from apps.reviews.services import ReviewService, build_target_reviews


class TargetReviewsView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, target_type: str, target_id: str):
        payload = build_target_reviews(target_type, target_id, user=request.user)
        return response.Response(TargetReviewPayloadSerializer(payload).data)

    def post(self, request, target_type: str, target_id: str):
        if not request.user or not request.user.is_authenticated:
            return response.Response({'detail': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
        serializer = ReviewCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        review = ReviewService.create_or_update_review(
            user=request.user,
            target_type=target_type,
            target_id=target_id,
            **serializer.validated_data,
        )
        return response.Response(ReviewSerializer(ReviewService.serialize_review(review)).data, status=status.HTTP_201_CREATED)


class AdminReviewTrustCenterView(views.APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        days = int(request.query_params.get('days') or 30)
        return response.Response(selectors.get_trust_overview(days=days))


class AdminPendingReviewListView(views.APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        status_value = request.query_params.get('status') or Review.STATUS_PENDING
        if status_value == 'all':
            queryset = Review.objects.all()
        else:
            queryset = Review.objects.filter(status=status_value)
        items = [ReviewService.serialize_review(review) for review in queryset.order_by('-created_at')[:200]]
        return response.Response({'results': ReviewSerializer(items, many=True).data})


class AdminReviewModerationView(views.APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, review_id: str):
        serializer = ReviewModerationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            review = Review.objects.filter(id=review_id).first()
        except (TypeError, ValueError):
            review = None
        if not review:
            raise NotFound('Review not found')
        updated = ReviewService.moderate_review(
            review=review,
            decision=serializer.validated_data['decision'],
            note=serializer.validated_data.get('note', ''),
            moderator=request.user,
        )
        return response.Response(ReviewSerializer(ReviewService.serialize_review(updated)).data)


class TrainerReviewQualityView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        days = int(request.query_params.get('days') or 30)
        return response.Response(selectors.get_trainer_quality_dashboard(trainer_user=request.user, days=days))


class TrainerReviewReplyView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, review_id: str):
        serializer = ReviewReplySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        review = Review.objects.filter(id=review_id).first()
        if not review:
            raise NotFound('Review not found')
        updated = ReviewService.reply_to_review(
            review=review,
            trainer=request.user,
            reply=serializer.validated_data['reply'],
        )
        return response.Response(ReviewSerializer(ReviewService.serialize_review(updated)).data)
