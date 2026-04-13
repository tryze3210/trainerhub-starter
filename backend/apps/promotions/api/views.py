from rest_framework import mixins, permissions, viewsets

from apps.promotions.api.serializers import PromoCampaignSerializer, PromoCodeSerializer
from apps.promotions.models import PromoCampaign, PromoCode
from apps.promotions.selectors import PromoSelector


class IsAdminUserStrict(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_staff)


class IsTrainerUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and hasattr(request.user, "trainer_profile"))


class AdminPromoCampaignViewSet(viewsets.ModelViewSet):
    serializer_class = PromoCampaignSerializer
    permission_classes = [IsAdminUserStrict]
    queryset = PromoCampaign.objects.all().select_related("trainer")


class AdminPromoCodeViewSet(viewsets.ModelViewSet):
    serializer_class = PromoCodeSerializer
    permission_classes = [IsAdminUserStrict]
    queryset = PromoCode.objects.all().select_related("campaign", "campaign__trainer")


class TrainerPromoCampaignViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = PromoCampaignSerializer
    permission_classes = [IsTrainerUser]

    def get_queryset(self):
        return PromoSelector.trainer_campaigns_with_stats(self.request.user.trainer_profile)
