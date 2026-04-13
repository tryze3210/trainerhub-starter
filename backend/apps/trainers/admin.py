from django.contrib import admin
from apps.trainers.models import TrainerProfile


@admin.register(TrainerProfile)
class TrainerProfileAdmin(admin.ModelAdmin):
    list_display = ("display_name", "slug", "user", "status", "is_public")
    search_fields = ("display_name", "slug", "user__email")
    list_filter = ("status", "is_public")
