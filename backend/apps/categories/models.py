from django.db import models
from apps.core.models import UUIDModel, TimeStampedModel


class Category(UUIDModel, TimeStampedModel):
    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=255)
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL, related_name="children")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return self.name


class Tag(UUIDModel, TimeStampedModel):
    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=255, unique=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return self.name
