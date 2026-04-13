from django.db import transaction
from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied
from apps.products.models import Product, ProductItem
from apps.videos.models import Video
from .serializers import ProductSerializer


class ProductListCreateApi(generics.ListCreateAPIView):
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    lookup_field = "slug"

    def get_queryset(self):
        qs = Product.objects.filter(is_deleted=False).prefetch_related("items")
        user = self.request.user
        if user.is_authenticated and user.role == "trainer" and hasattr(user, "trainer_profile"):
            return qs.filter(trainer=user.trainer_profile)
        return qs.filter(status="published")

    @transaction.atomic
    def perform_create(self, serializer):
        if not self.request.user.is_authenticated or self.request.user.role != "trainer" or not hasattr(self.request.user, "trainer_profile"):
            raise PermissionDenied("Only trainers can create products.")
        trainer = self.request.user.trainer_profile
        item_video_ids = serializer.validated_data.pop("item_video_ids", [])
        product = serializer.save(trainer=trainer)
        if item_video_ids:
            videos = list(Video.objects.filter(id__in=item_video_ids, trainer=trainer, status="ready"))
            ProductItem.objects.bulk_create(
                [ProductItem(product=product, video=video, position=index) for index, video in enumerate(videos)]
            )


class ProductDetailApi(generics.RetrieveUpdateAPIView):
    serializer_class = ProductSerializer
    lookup_field = "slug"

    def get_queryset(self):
        qs = Product.objects.filter(is_deleted=False).prefetch_related("items")
        user = self.request.user
        if user.is_authenticated and user.role == "trainer" and hasattr(user, "trainer_profile"):
            return qs.filter(trainer=user.trainer_profile)
        return qs.filter(status="published")

    @transaction.atomic
    def perform_update(self, serializer):
        product = self.get_object()
        user = self.request.user
        if not user.is_authenticated or user.role != "trainer" or not hasattr(user, "trainer_profile") or product.trainer_id != user.trainer_profile.id:
            raise PermissionDenied("You cannot update this product.")
        item_video_ids = serializer.validated_data.pop("item_video_ids", None)
        product = serializer.save()
        if item_video_ids is not None:
            ProductItem.objects.filter(product=product).delete()
            videos = list(Video.objects.filter(id__in=item_video_ids, trainer=product.trainer, status="ready"))
            ProductItem.objects.bulk_create(
                [ProductItem(product=product, video=video, position=index) for index, video in enumerate(videos)]
            )
