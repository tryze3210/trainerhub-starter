from django.db.models import Count
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.notifications.api.serializers import (
    AdminAnnouncementCreateSerializer,
    AdminAnnouncementSerializer,
    NotificationDeliverySerializer,
    NotificationPreferenceSerializer,
    NotificationTemplateSerializer,
)
from apps.notifications.models import AdminAnnouncement, Notification, NotificationDelivery, NotificationPreference, NotificationTemplate
from apps.notifications.selectors import NotificationEngagementSelectors
from apps.notifications.services import AdminAnnouncementService


class IsAdminUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_staff)


class UserNotificationInboxView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        unread_only = request.query_params.get('unread') in {'1', 'true', 'True'}
        limit = int(request.query_params.get('limit') or 50)
        return Response(NotificationEngagementSelectors.user_inbox(user=request.user, unread_only=unread_only, limit=limit))


class UserNotificationMarkReadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, notification_id: str):
        notification = get_object_or_404(Notification, notification_uuid=notification_id, user=request.user)
        notification.mark_read()
        return Response(NotificationEngagementSelectors.serialize_notification(notification))


class UserNotificationMarkAllReadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        qs = Notification.objects.filter(user=request.user, is_read=False)
        count = qs.count()
        for notification in qs.iterator(chunk_size=200):
            notification.mark_read()
        return Response({'updated': count})


class UserNotificationPreferenceView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        obj, _ = NotificationPreference.objects.get_or_create(user=self.request.user)
        return obj

    def get(self, request):
        return Response(NotificationPreferenceSerializer(self.get_object()).data)

    def patch(self, request):
        serializer = NotificationPreferenceSerializer(self.get_object(), data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class AdminNotificationCenterView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]

    def get(self, request):
        days = int(request.query_params.get('days') or 30)
        return Response(NotificationEngagementSelectors.admin_center(days=days))


class AdminAnnouncementListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]

    def get(self, request):
        qs = AdminAnnouncement.objects.select_related('created_by').annotate(notifications_count=Count('notifications')).order_by('-created_at')
        published = request.query_params.get('published')
        if published in {'true', '1'}:
            qs = qs.filter(is_published=True)
        elif published in {'false', '0'}:
            qs = qs.filter(is_published=False)
        return Response({'results': AdminAnnouncementSerializer(qs[:100], many=True).data})

    def post(self, request):
        serializer = AdminAnnouncementCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        announcement, created_count = AdminAnnouncementService.create_announcement(actor=request.user, **serializer.validated_data)
        payload = AdminAnnouncementSerializer(announcement).data
        payload['created_notifications'] = created_count
        return Response(payload, status=status.HTTP_201_CREATED)


class AdminAnnouncementDetailView(generics.RetrieveUpdateAPIView):
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    serializer_class = AdminAnnouncementSerializer
    lookup_field = 'announcement_uuid'
    lookup_url_kwarg = 'announcement_id'
    queryset = AdminAnnouncement.objects.select_related('created_by').all()


class AdminAnnouncementPublishView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]

    def post(self, request, announcement_id: str):
        announcement = get_object_or_404(AdminAnnouncement, announcement_uuid=announcement_id)
        created_count = AdminAnnouncementService.publish(
            announcement=announcement,
            actor=request.user,
            user_ids=request.data.get('user_ids'),
        )
        payload = AdminAnnouncementSerializer(announcement).data
        payload['created_notifications'] = created_count
        return Response(payload)


class AdminNotificationTemplateListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    serializer_class = NotificationTemplateSerializer
    queryset = NotificationTemplate.objects.order_by('code')


class AdminNotificationTemplateDetailView(generics.RetrieveUpdateAPIView):
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    serializer_class = NotificationTemplateSerializer
    queryset = NotificationTemplate.objects.all()


class AdminNotificationDeliveryListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    serializer_class = NotificationDeliverySerializer

    def get_queryset(self):
        qs = NotificationDelivery.objects.select_related('user').order_by('-created_at')
        status_value = self.request.query_params.get('status')
        channel = self.request.query_params.get('channel')
        type_value = self.request.query_params.get('type')
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
            'total': qs.count(),
            'pending': qs.filter(status='pending').count(),
            'sent': qs.filter(status='sent').count(),
            'failed': qs.filter(status='failed').count(),
            'email': qs.filter(channel='email').count(),
            'in_app_linked': qs.filter(notification__isnull=False).count(),
        })


from apps.events.services import DomainEventService
from apps.notifications.api.serializers import (
    NotificationProjectionHealthSerializer,
    NotificationProjectionRunSerializer,
)
from apps.notifications.projections import notification_projection_service


class AdminNotificationProjectionHealthView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]

    def get(self, request):
        serializer = NotificationProjectionHealthSerializer(notification_projection_service.projection_health())
        return Response(serializer.data)


class AdminNotificationProjectOutboxView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]

    def post(self, request):
        serializer = NotificationProjectionRunSerializer(data=request.data or {})
        serializer.is_valid(raise_exception=True)
        result = DomainEventService().dispatch_pending_batch(batch_size=serializer.validated_data['batch_size'])
        return Response(result, status=status.HTTP_202_ACCEPTED)
