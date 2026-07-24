from django.db import transaction
from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied
from apps.access_control.permissions import ROLE_TRAINER, user_role_set
from apps.products.models import Product, ProductItem
from apps.videos.models import Video
from .serializers import ProductSerializer


def _trainer_profile_for(user):
    if not getattr(user, "is_authenticated", False):
        return None
    if ROLE_TRAINER not in user_role_set(user):
        return None
    return getattr(user, "trainer_profile", None)


class ProductListCreateApi(generics.ListCreateAPIView):
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    lookup_field = "slug"

    def get_queryset(self):
        qs = Product.objects.filter(is_deleted=False).prefetch_related("items")
        trainer_profile = _trainer_profile_for(self.request.user)
        if trainer_profile is not None:
            return qs.filter(trainer=trainer_profile)
        return qs.filter(status="published")

    @transaction.atomic
    def perform_create(self, serializer):
        trainer = _trainer_profile_for(self.request.user)
        if trainer is None:
            raise PermissionDenied("Only trainers can create products.")
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
        trainer_profile = _trainer_profile_for(self.request.user)
        if trainer_profile is not None:
            return qs.filter(trainer=trainer_profile)
        return qs.filter(status="published")

    @transaction.atomic
    def perform_update(self, serializer):
        product = self.get_object()
        trainer_profile = _trainer_profile_for(self.request.user)
        if trainer_profile is None or product.trainer_id != trainer_profile.id:
            raise PermissionDenied("You cannot update this product.")
        item_video_ids = serializer.validated_data.pop("item_video_ids", None)
        product = serializer.save()
        if item_video_ids is not None:
            ProductItem.objects.filter(product=product).delete()
            videos = list(Video.objects.filter(id__in=item_video_ids, trainer=product.trainer, status="ready"))
            ProductItem.objects.bulk_create(
                [ProductItem(product=product, video=video, position=index) for index, video in enumerate(videos)]
            )
