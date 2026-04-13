from apps.cohorts.models import Cohort, CohortDashboardSnapshot


class CohortDashboardSelectors:
    @staticmethod
    def trainer_cohorts(trainer_id):
        return Cohort.objects.filter(program__trainer_id=trainer_id).select_related("program").order_by("-starts_at")

    @staticmethod
    def latest_snapshot(cohort_id):
        return CohortDashboardSnapshot.objects.filter(cohort_id=cohort_id).order_by("-snapshot_date").first()
