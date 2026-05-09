from __future__ import annotations

from rest_framework import serializers


SOURCE_CHOICES = (
    ('', 'Any'),
    ('manual', 'Manual'),
    ('scheduled', 'Scheduled'),
    ('repair', 'Repair'),
    ('ci', 'CI'),
)

CAPTURE_SOURCE_CHOICES = (
    ('manual', 'Manual'),
    ('scheduled', 'Scheduled'),
    ('repair', 'Repair'),
    ('ci', 'CI'),
)

STATUS_CHOICES = (
    ('', 'Any'),
    ('ok', 'OK'),
    ('degraded', 'Degraded'),
    ('critical', 'Critical'),
)


ISSUE_SEVERITY_CHOICES = (
    ('', 'Any'),
    ('critical', 'Critical'),
    ('warning', 'Warning'),
    ('info', 'Info'),
)

REPAIRABLE_CHOICES = (
    ('', 'Any'),
    ('true', 'Repairable'),
    ('false', 'Not repairable'),
)



class AdminReconciliationSnapshotListSerializer(serializers.Serializer):
    limit = serializers.IntegerField(required=False, min_value=1, max_value=250, default=20)
    source = serializers.ChoiceField(required=False, allow_blank=True, choices=SOURCE_CHOICES, default='')
    status = serializers.ChoiceField(required=False, allow_blank=True, choices=STATUS_CHOICES, default='')
    include_report = serializers.BooleanField(required=False, default=False)


class AdminReconciliationSnapshotCaptureSerializer(serializers.Serializer):
    limit = serializers.IntegerField(required=False, min_value=1, max_value=500, default=100)
    source = serializers.ChoiceField(required=False, choices=CAPTURE_SOURCE_CHOICES, default='manual')
    correlation_id = serializers.CharField(required=False, allow_blank=True, max_length=128)


class AdminReconciliationSnapshotLatestSerializer(serializers.Serializer):
    source = serializers.ChoiceField(required=False, allow_blank=True, choices=SOURCE_CHOICES, default='')
    status = serializers.ChoiceField(required=False, allow_blank=True, choices=STATUS_CHOICES, default='')
    include_report = serializers.BooleanField(required=False, default=False)


class AdminReconciliationSnapshotTrendSerializer(serializers.Serializer):
    limit = serializers.IntegerField(required=False, min_value=2, max_value=250, default=30)


class AdminReconciliationSnapshotMetricsSerializer(serializers.Serializer):
    limit = serializers.IntegerField(required=False, min_value=2, max_value=250, default=30)
    source = serializers.ChoiceField(required=False, allow_blank=True, choices=SOURCE_CHOICES, default='')
    status = serializers.ChoiceField(required=False, allow_blank=True, choices=STATUS_CHOICES, default='')


class AdminReconciliationSnapshotAlertSerializer(serializers.Serializer):
    source = serializers.ChoiceField(required=False, allow_blank=True, choices=SOURCE_CHOICES, default='')
    min_total_delta = serializers.IntegerField(required=False, min_value=0, max_value=10000, default=1)
    min_critical_delta = serializers.IntegerField(required=False, min_value=0, max_value=10000, default=1)
    stale_after_minutes = serializers.IntegerField(required=False, min_value=1, max_value=43200, default=180)
    notify_admins = serializers.BooleanField(required=False, default=True)
    dedupe_hours = serializers.IntegerField(required=False, min_value=1, max_value=720, default=24)


class AdminReconciliationSnapshotScheduleSerializer(serializers.Serializer):
    source = serializers.ChoiceField(
        required=False,
        choices=(
            ('scheduled', 'Scheduled'),
            ('manual', 'Manual'),
            ('ci', 'CI'),
        ),
        default='scheduled',
    )
    min_age_minutes = serializers.IntegerField(required=False, min_value=1, max_value=10080, default=60)


class AdminReconciliationSnapshotCompareSerializer(serializers.Serializer):
    baseline_id = serializers.UUIDField(required=False)
    current_id = serializers.UUIDField(required=False)
    source = serializers.ChoiceField(required=False, allow_blank=True, choices=SOURCE_CHOICES, default='')
    include_report = serializers.BooleanField(required=False, default=False)
    diff_limit = serializers.IntegerField(required=False, min_value=1, max_value=500, default=100)



class AdminReconciliationSnapshotRetentionSerializer(serializers.Serializer):
    source = serializers.ChoiceField(required=False, allow_blank=True, choices=SOURCE_CHOICES, default='')
    scheduled_days = serializers.IntegerField(required=False, min_value=1, max_value=3650, default=45)
    repair_days = serializers.IntegerField(required=False, min_value=1, max_value=3650, default=180)
    manual_days = serializers.IntegerField(required=False, min_value=1, max_value=3650, default=365)
    ci_days = serializers.IntegerField(required=False, min_value=1, max_value=3650, default=14)
    keep_min_per_source = serializers.IntegerField(required=False, min_value=1, max_value=500, default=25)
    max_candidates = serializers.IntegerField(required=False, min_value=1, max_value=5000, default=500)
    include_candidates = serializers.BooleanField(required=False, default=True)
    dry_run = serializers.BooleanField(required=False, default=True)


class AdminReconciliationIssueRegistrySerializer(serializers.Serializer):
    snapshot_id = serializers.UUIDField(required=False)
    source = serializers.ChoiceField(required=False, allow_blank=True, choices=SOURCE_CHOICES, default='')
    status = serializers.ChoiceField(required=False, allow_blank=True, choices=STATUS_CHOICES, default='')
    issue_code = serializers.CharField(required=False, allow_blank=True, max_length=128, default='')
    severity = serializers.ChoiceField(required=False, allow_blank=True, choices=ISSUE_SEVERITY_CHOICES, default='')
    entity_type = serializers.CharField(required=False, allow_blank=True, max_length=80, default='')
    entity_id = serializers.CharField(required=False, allow_blank=True, max_length=128, default='')
    section = serializers.CharField(required=False, allow_blank=True, max_length=80, default='')
    repairable = serializers.ChoiceField(required=False, allow_blank=True, choices=REPAIRABLE_CHOICES, default='')
    limit = serializers.IntegerField(required=False, min_value=1, max_value=500, default=100)
    include_report = serializers.BooleanField(required=False, default=False)

