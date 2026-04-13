from rest_framework import serializers

from apps.cohorts.models import Cohort, CohortDashboardSnapshot, CohortEnrollment, GroupProgram, ProgressCheckpoint


class GroupProgramSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupProgram
        fields = [
            "id", "trainer", "title", "slug", "description", "status",
            "starts_at", "ends_at", "is_paid", "price_amount", "currency",
        ]
        read_only_fields = ["id", "trainer"]


class CohortSerializer(serializers.ModelSerializer):
    program = GroupProgramSerializer(read_only=True)

    class Meta:
        model = Cohort
        fields = ["id", "program", "code", "title", "status", "starts_at", "ends_at", "capacity", "timezone"]


class ProgressCheckpointSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProgressCheckpoint
        fields = ["id", "title", "checkpoint_type", "sequence", "due_at", "is_required"]


class CohortEnrollmentSerializer(serializers.ModelSerializer):
    cohort = CohortSerializer(read_only=True)

    class Meta:
        model = CohortEnrollment
        fields = ["id", "cohort", "status", "activated_at", "completed_at", "cancelled_at", "source", "order_id"]


class CohortDashboardSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = CohortDashboardSnapshot
        fields = [
            "snapshot_date", "enrolled_count", "active_count", "completed_count",
            "completion_rate", "avg_checkpoint_progress", "attendance_rate",
        ]
