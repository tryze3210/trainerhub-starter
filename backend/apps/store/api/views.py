from rest_framework import permissions, viewsets
from rest_framework.response import Response
from apps.store.selectors import list_bundles, list_programs, list_videos


class VideoStoreViewSet(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny]

    def list(self, request):
        return Response(list_videos())


class ProgramStoreViewSet(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny]

    def list(self, request):
        return Response(list_programs())


class BundleStoreViewSet(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny]

    def list(self, request):
        return Response(list_bundles())
