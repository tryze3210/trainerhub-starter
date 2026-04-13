from rest_framework import generics
from apps.categories.models import Category, Tag
from .serializers import CategorySerializer, TagSerializer


class CategoryListApi(generics.ListAPIView):
    serializer_class = CategorySerializer
    queryset = Category.objects.filter(is_active=True).select_related("parent")


class TagListApi(generics.ListAPIView):
    serializer_class = TagSerializer
    queryset = Tag.objects.filter(is_active=True)
