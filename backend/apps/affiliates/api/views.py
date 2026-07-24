from rest_framework import mixins, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle

from apps.affiliates.api.serializers import (
    AffiliateClickCaptureSerializer,
    AffiliateCommissionSerializer,
    AffiliatePartnerSerializer,
    OrderAttributionSerializer,
)
from apps.affiliates.models import AffiliateCommission, AffiliatePartner, AffiliatePartnerStatus, OrderAttribution
from apps.affiliates.services import AffiliateCommissionService, AffiliateTrackingService


class IsAdminUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_staff)


class IsAffiliatePartnerUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and hasattr(request.user, "affiliate_partner"))


class AdminAffiliatePartnerViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    queryset = AffiliatePartner.objects.select_related("trainer", "user").all()
    serializer_class = AffiliatePartnerSerializer


class AdminAffiliateCommissionViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    permission_classes = [IsAdminUser]
    queryset = AffiliateCommission.objects.select_related("partner", "order_attribution").all()
    serializer_class = AffiliateCommissionSerializer

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        commission = self.get_object()
        AffiliateCommissionService.approve_commission(commission=commission)
        return Response(self.get_serializer(commission).data)

    @action(detail=True, methods=["post"])
    def reverse(self, request, pk=None):
        commission = self.get_object()
        AffiliateCommissionService.reverse_commission(commission=commission)
        return Response(self.get_serializer(commission).data)


class AffiliatePartnerDashboardViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    permission_classes = [IsAffiliatePartnerUser]
    serializer_class = AffiliateCommissionSerializer

    def get_queryset(self):
        return AffiliateCommission.objects.filter(partner=self.request.user.affiliate_partner).select_related("order_attribution")


class AffiliateOrderAttributionViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    permission_classes = [IsAdminUser]
    queryset = OrderAttribution.objects.select_related("partner", "order").all()
    serializer_class = OrderAttributionSerializer


class PublicAffiliateTrackingViewSet(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "affiliate_click"

    @action(detail=False, methods=["post"], url_path="click")
    def click(self, request):
        serializer = AffiliateClickCaptureSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data
        result = AffiliateTrackingService.capture_click(
            partner_code=payload["partner_code"],
            client_key=payload["client_key"],
            landing_path=payload.get("landing_path", ""),
            referrer_url=payload.get("referrer_url", ""),
            utm=payload.get("utm") or {},
            user=request.user,
            ip_address=request.META.get("REMOTE_ADDR"),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
        )
        return Response({
            "partner_id": result.partner_id,
            "click_id": result.click_id,
            "attribution_id": result.attribution_id,
            "status": AffiliatePartnerStatus.ACTIVE,
        })
