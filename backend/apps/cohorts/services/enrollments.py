from django.db import transaction
from django.utils import timezone

from apps.cohorts.models import CohortEnrollment, EnrollmentCheckpointProgress


class EnrollmentLifecycleService:
    @staticmethod
    @transaction.atomic
    def activate(enrollment: CohortEnrollment) -> CohortEnrollment:
        if enrollment.status == CohortEnrollment.STATUS_ACTIVE:
            return enrollment
        enrollment.status = CohortEnrollment.STATUS_ACTIVE
        enrollment.activated_at = enrollment.activated_at or timezone.now()
        enrollment.save(update_fields=["status", "activated_at", "updated_at"])

        checkpoints = enrollment.cohort.checkpoints.all()
        existing = set(
            EnrollmentCheckpointProgress.objects.filter(enrollment=enrollment).values_list("checkpoint_id", flat=True)
        )
        to_create = [
            EnrollmentCheckpointProgress(enrollment=enrollment, checkpoint=checkpoint)
            for checkpoint in checkpoints
            if checkpoint.id not in existing
        ]
        if to_create:
            EnrollmentCheckpointProgress.objects.bulk_create(to_create)
        return enrollment

    @staticmethod
    @transaction.atomic
    def complete(enrollment: CohortEnrollment) -> CohortEnrollment:
        enrollment.status = CohortEnrollment.STATUS_COMPLETED
        enrollment.completed_at = timezone.now()
        enrollment.save(update_fields=["status", "completed_at", "updated_at"])
        return enrollment
