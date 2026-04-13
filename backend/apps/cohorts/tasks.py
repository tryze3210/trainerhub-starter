from celery import shared_task

from apps.cohorts.models import Cohort
from apps.cohorts.services.dashboard import CohortDashboardBuilder


@shared_task(name="cohorts.rebuild_all_dashboards")
def rebuild_all_dashboards():
    for cohort in Cohort.objects.all().iterator():
        CohortDashboardBuilder.rebuild_for_cohort(cohort)
