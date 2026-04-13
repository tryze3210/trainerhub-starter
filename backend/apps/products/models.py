from django.db import models
from apps.core.models import UUIDModel, TimeStampedModel, SoftDeleteModel
from apps.trainers.models import TrainerProfile
from apps.videos.models import Video


class Product(UUIDModel, TimeStampedModel, SoftDeleteModel):
    trainer = models.ForeignKey(TrainerProfile, on_delete=models.CASCADE, related_name="products")
    slug = models.SlugField(max_length=160, unique=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    product_type = models.CharField(max_length=32)
    access_type = models.CharField(max_length=32)
    status = models.CharField(max_length=32, default="draft")
    currency = models.CharField(max_length=8, default="RUB")
    price_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def __str__(self):
        return self.title


class ProductItem(UUIDModel, TimeStampedModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="items")
    video = models.ForeignKey(Video, on_delete=models.CASCADE)
    position = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("product", "video")
        ordering = ("position",)
