from rest_framework import generics, permissions, response, status, views

from apps.cohorts.api.serializers import CohortDashboardSnapshotSerializer, CohortEnrollmentSerializer, CohortSerializer
from apps.cohorts.models import Cohort, CohortEnrollment
from apps.cohorts.selectors.dashboard import CohortDashboardSelectors
from apps.cohorts.services.dashboard import CohortDashboardBuilder


class MyCohortEnrollmentsView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CohortEnrollmentSerializer

    def get_queryset(self):
        return CohortEnrollment.objects.filter(user=self.request.user).select_related("cohort", "cohort__program")


class TrainerCohortsView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CohortSerializer

    def get_queryset(self):
        return CohortDashboardSelectors.trainer_cohorts(self.request.user.id)


class CohortDashboardView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, cohort_id):
        cohort = Cohort.objects.get(id=cohort_id)
        snapshot = CohortDashboardSelectors.latest_snapshot(cohort.id)
        if snapshot is None:
            snapshot = CohortDashboardBuilder.rebuild_for_cohort(cohort)
        return response.Response(CohortDashboardSnapshotSerializer(snapshot).data)


class RebuildCohortDashboardView(views.APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, cohort_id):
        cohort = Cohort.objects.get(id=cohort_id)
        snapshot = CohortDashboardBuilder.rebuild_for_cohort(cohort)
        return response.Response(CohortDashboardSnapshotSerializer(snapshot).data, status=status.HTTP_200_OK)
