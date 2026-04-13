from rest_framework import permissions, viewsets
from apps.content.api.serializers import PublishedBundleSerializer, PublishedProgramSerializer, PublishedVideoSerializer
from apps.content.models import PublishedBundle, PublishedProgram, PublishedVideo


class PublishedVideoViewSet(viewsets.ReadOnlyModelViewSet):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]
    queryset = PublishedVideo.objects.select_related('trainer_profile').filter(is_active=True, visibility='public')
    serializer_class = PublishedVideoSerializer
    lookup_field = 'slug'


class PublishedProgramViewSet(viewsets.ReadOnlyModelViewSet):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]
    queryset = PublishedProgram.objects.select_related('trainer_profile').prefetch_related('lessons').filter(is_active=True, visibility='public')
    serializer_class = PublishedProgramSerializer
    lookup_field = 'slug'


class PublishedBundleViewSet(viewsets.ReadOnlyModelViewSet):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]
    queryset = PublishedBundle.objects.select_related('trainer_profile').prefetch_related('items').filter(is_active=True, visibility='public')
    serializer_class = PublishedBundleSerializer
    lookup_field = 'slug'
