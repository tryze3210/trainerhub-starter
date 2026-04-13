from decimal import Decimal
from django.db.models import Avg, Count, Q
from django.utils import timezone

from apps.cohorts.models import Cohort, CohortDashboardSnapshot, CohortEnrollment, EnrollmentCheckpointProgress


class CohortDashboardBuilder:
    @staticmethod
    def rebuild_for_cohort(cohort: Cohort) -> CohortDashboardSnapshot:
        enrollments = CohortEnrollment.objects.filter(cohort=cohort)
        enrolled_count = enrollments.count()
        active_count = enrollments.filter(status=CohortEnrollment.STATUS_ACTIVE).count()
        completed_count = enrollments.filter(status=CohortEnrollment.STATUS_COMPLETED).count()

        completion_rate = Decimal("0.00")
        if enrolled_count:
            completion_rate = Decimal(completed_count * 100 / enrolled_count).quantize(Decimal("0.01"))

        progress_agg = EnrollmentCheckpointProgress.objects.filter(enrollment__cohort=cohort).aggregate(
            avg_done=Avg(
                Q(status=EnrollmentCheckpointProgress.STATUS_DONE)
            )
        )
        # Placeholder until project-specific attendance/live-session integration is wired.
        avg_checkpoint_progress = Decimal("0.00")
        attendance_rate = Decimal("0.00")
        if progress_agg["avg_done"] is not None:
            avg_checkpoint_progress = Decimal(str(progress_agg["avg_done"] * 100)).quantize(Decimal("0.01"))

        snapshot, _ = CohortDashboardSnapshot.objects.update_or_create(
            cohort=cohort,
            snapshot_date=timezone.localdate(),
            defaults={
                "enrolled_count": enrolled_count,
                "active_count": active_count,
                "completed_count": completed_count,
                "completion_rate": completion_rate,
                "avg_checkpoint_progress": avg_checkpoint_progress,
                "attendance_rate": attendance_rate,
            },
        )
        return snapshot
