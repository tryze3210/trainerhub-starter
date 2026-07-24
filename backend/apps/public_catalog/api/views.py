from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.public_catalog import selectors, services
from apps.public_catalog.api.serializers import (
    CatalogResponseSerializer,
    PublicCatalogItemSerializer,
    PublicContentLandingSerializer,
    PublicMarketplaceHomeSerializer,
    PublicTrainerLandingSerializer,
)


class PublicCatalogView(APIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        payload = services.build_catalog_response(request.query_params)
        serializer = CatalogResponseSerializer(payload)
        return Response(serializer.data)


class FeaturedCatalogView(APIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        serializer = PublicCatalogItemSerializer(selectors.list_featured_items(), many=True)
        return Response(serializer.data)


class PublicCatalogItemDetailView(APIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def get(self, request, entity_type: str, slug: str):
        item = services.get_public_item_or_raise(entity_type, slug)
        return Response(PublicCatalogItemSerializer(item).data)


class PublicMarketplaceHomeView(APIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        payload = services.build_marketplace_home(request.query_params)
        return Response(PublicMarketplaceHomeSerializer(payload).data)


class PublicContentLandingView(APIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def get(self, request, entity_type: str, slug: str):
        payload = services.build_content_landing(entity_type, slug)
        return Response(PublicContentLandingSerializer(payload).data)


class PublicTrainerLandingView(APIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def get(self, request, slug: str):
        payload = services.build_trainer_landing(slug)
        return Response(PublicTrainerLandingSerializer(payload).data)
