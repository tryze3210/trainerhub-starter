from rest_framework import permissions, viewsets
from rest_framework.response import Response

from apps.content.api.serializers import (
    PublishedBundleSerializer,
    PublishedProgramSerializer,
    PublishedVideoSerializer,
)
from apps.content.models import PublishedBundle, PublishedProgram, PublishedVideo


class NonPaginatedPublicContentMixin:
    """
    Public catalog endpoints are intentionally returned as plain JSON arrays.

    The frontend catalog and the existing API contracts both treat these routes
    as lightweight public lists, not admin-style paginated collections. Keeping
    pagination disabled here prevents the global DRF pagination setting from
    wrapping responses into {count, next, previous, results}.
    """

    pagination_class = None

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class PublishedVideoViewSet(NonPaginatedPublicContentMixin, viewsets.ReadOnlyModelViewSet):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]
    queryset = PublishedVideo.objects.select_related('trainer_profile').filter(is_active=True, visibility='public')
    serializer_class = PublishedVideoSerializer
    lookup_field = 'slug'


class PublishedProgramViewSet(NonPaginatedPublicContentMixin, viewsets.ReadOnlyModelViewSet):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]
    queryset = PublishedProgram.objects.select_related('trainer_profile').prefetch_related('lessons').filter(is_active=True, visibility='public')
    serializer_class = PublishedProgramSerializer
    lookup_field = 'slug'


class PublishedBundleViewSet(NonPaginatedPublicContentMixin, viewsets.ReadOnlyModelViewSet):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]
    queryset = PublishedBundle.objects.select_related('trainer_profile').prefetch_related('items').filter(is_active=True, visibility='public')
    serializer_class = PublishedBundleSerializer
    lookup_field = 'slug'
