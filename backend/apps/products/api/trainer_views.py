from __future__ import annotations

from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.products.api.trainer_serializers import TrainerProductReadinessSerializer, TrainerProductSerializer
from apps.products.services import TrainerProductBuilderService


class TrainerProductBuilderViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]
    service = TrainerProductBuilderService()

    def _serialize(self, product):
        product._readiness = self.service.readiness(product=product)
        return TrainerProductSerializer(product).data

    def list(self, request):
        products = self.service.list_products(user=request.user)
        return Response([self._serialize(product) for product in products])

    def retrieve(self, request, pk=None):
        product = self.service.get_product(user=request.user, product_id=pk)
        return Response(self._serialize(product))

    def create(self, request):
        serializer = TrainerProductSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product = self.service.create_product(user=request.user, payload=dict(serializer.validated_data))
        return Response(self._serialize(product), status=status.HTTP_201_CREATED)

    def update(self, request, pk=None):
        serializer = TrainerProductSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product = self.service.update_product(user=request.user, product_id=pk, payload=dict(serializer.validated_data), partial=False)
        return Response(self._serialize(product))

    def partial_update(self, request, pk=None):
        serializer = TrainerProductSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        product = self.service.update_product(user=request.user, product_id=pk, payload=dict(serializer.validated_data), partial=True)
        return Response(self._serialize(product))

    def destroy(self, request, pk=None):
        self.service.soft_delete_product(user=request.user, product_id=pk)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["get"], url_path="readiness")
    def readiness(self, request, pk=None):
        product = self.service.get_product(user=request.user, product_id=pk)
        payload = self.service.readiness(product=product)
        return Response(TrainerProductReadinessSerializer(payload).data)

    @action(detail=True, methods=["post"], url_path="publish")
    def publish(self, request, pk=None):
        product = self.service.publish_product(user=request.user, product_id=pk)
        return Response(self._serialize(product))

    @action(detail=True, methods=["post"], url_path="archive")
    def archive(self, request, pk=None):
        product = self.service.archive_product(user=request.user, product_id=pk)
        return Response(self._serialize(product))
