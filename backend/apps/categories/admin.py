from django.contrib import admin
from apps.categories.models import Category, Tag

admin.site.register(Category)
admin.site.register(Tag)
