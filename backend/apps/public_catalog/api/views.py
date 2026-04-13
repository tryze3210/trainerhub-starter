from rest_framework.response import Response
from rest_framework.views import APIView

from apps.public_catalog import selectors, services
from apps.public_catalog.api.serializers import CatalogResponseSerializer, PublicCatalogItemSerializer


class PublicCatalogView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        payload = services.build_catalog_response(request.query_params)
        serializer = CatalogResponseSerializer(payload)
        return Response(serializer.data)


class FeaturedCatalogView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        serializer = PublicCatalogItemSerializer(selectors.list_featured_items(), many=True)
        return Response(serializer.data)


class PublicCatalogItemDetailView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, entity_type: str, slug: str):
        item = services.get_public_item_or_raise(entity_type, slug)
        return Response(PublicCatalogItemSerializer(item).data)
