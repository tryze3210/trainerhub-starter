from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.notifications.models import NotificationTemplate, NotificationDelivery
from apps.notifications.api.serializers import NotificationTemplateSerializer, NotificationDeliverySerializer


class IsAdminUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_staff)


class AdminNotificationTemplateListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    serializer_class = NotificationTemplateSerializer
    queryset = NotificationTemplate.objects.order_by("code")


class AdminNotificationTemplateDetailView(generics.RetrieveUpdateAPIView):
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    serializer_class = NotificationTemplateSerializer
    queryset = NotificationTemplate.objects.all()


class AdminNotificationDeliveryListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    serializer_class = NotificationDeliverySerializer

    def get_queryset(self):
        qs = NotificationDelivery.objects.select_related("user").order_by("-created_at")
        status_value = self.request.query_params.get("status")
        channel = self.request.query_params.get("channel")
        type_value = self.request.query_params.get("type")
        if status_value:
            qs = qs.filter(status=status_value)
        if channel:
            qs = qs.filter(channel=channel)
        if type_value:
            qs = qs.filter(type=type_value)
        return qs


class AdminNotificationDeliveryOverviewView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]

    def get(self, request):
        qs = NotificationDelivery.objects.all()
        return Response({
            "total": qs.count(),
            "pending": qs.filter(status="pending").count(),
            "sent": qs.filter(status="sent").count(),
            "failed": qs.filter(status="failed").count(),
            "email": qs.filter(channel="email").count(),
            "in_app_linked": qs.filter(notification__isnull=False).count(),
        })
