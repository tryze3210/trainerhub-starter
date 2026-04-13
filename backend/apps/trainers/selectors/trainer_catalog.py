from apps.trainers.models import TrainerProfile


def get_public_trainer_catalog_queryset():
    return (
        TrainerProfile.objects
        .filter(is_public=True, status__in=["pending", "approved"], is_deleted=False)
        .select_related("user")
        .order_by("-views_count", "-created_at")
    )
