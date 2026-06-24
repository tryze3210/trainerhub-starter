from __future__ import annotations

from rest_framework import serializers


SOURCE_CHOICES = (
    ('', 'Any'),
    ('manual', 'Manual'),
    ('scheduled', 'Scheduled'),
    ('repair', 'Repair'),
    ('ci', 'CI'),
)


class OperationsIssueSerializer(serializers.Serializer):
    code = serializers.CharField()
    severity = serializers.CharField()
    count = serializers.IntegerField(required=False)
    amount = serializers.CharField(required=False)


class OperationsSectionSerializer(serializers.Serializer):
    status = serializers.CharField()
    issues = OperationsIssueSerializer(many=True)
    counts = serializers.DictField(required=False)
    amounts = serializers.DictField(required=False)
    by_status = serializers.ListField(child=serializers.DictField(), required=False)
    risk_amounts = serializers.DictField(required=False)
    payout_request_by_status = serializers.ListField(child=serializers.DictField(), required=False)
    case_by_status = serializers.ListField(child=serializers.DictField(), required=False)
    flag_by_level = serializers.ListField(child=serializers.DictField(), required=False)
    recent_problem_messages = serializers.ListField(child=serializers.DictField(), required=False)
    recent_problem_events = serializers.ListField(child=serializers.DictField(), required=False)
    recent_risk_payments = serializers.ListField(child=serializers.DictField(), required=False)
    recent_risk_ledger_entries = serializers.ListField(child=serializers.DictField(), required=False)
    recent_payment_risk_cases = serializers.ListField(child=serializers.DictField(), required=False)


class AdminOperationsDashboardSerializer(serializers.Serializer):
    status = serializers.CharField()
    generated_at = serializers.DateTimeField()
    # The section keys are stable, but DictField keeps this serializer tolerant
    # as more operational sections are added in future patches.
    sections = serializers.DictField()
    summary = serializers.DictField()


class AdminOperationsHubQuerySerializer(serializers.Serializer):
    snapshot_limit = serializers.IntegerField(required=False, min_value=2, max_value=250, default=30)
    issue_limit = serializers.IntegerField(required=False, min_value=1, max_value=250, default=20)
    source = serializers.ChoiceField(required=False, allow_blank=True, choices=SOURCE_CHOICES, default='')
    include_issues = serializers.BooleanField(required=False, default=True)
    include_alerts = serializers.BooleanField(required=False, default=True)


class AdminOperationsHubSerializer(serializers.Serializer):
    status = serializers.CharField()
    generated_at = serializers.DateTimeField()
    filters = serializers.DictField()
    summary = serializers.DictField()
    sections = serializers.DictField()
    raw_operations_dashboard = serializers.DictField(required=False)
    quick_actions = serializers.ListField(child=serializers.DictField())
    navigation = serializers.ListField(child=serializers.DictField())


class AdminOperationsReadinessQuerySerializer(serializers.Serializer):
    include_commands = serializers.BooleanField(required=False, default=True)
    include_recommendations = serializers.BooleanField(required=False, default=True)


class AdminOperationsReadinessSerializer(serializers.Serializer):
    status = serializers.CharField()
    generated_at = serializers.DateTimeField()
    version = serializers.CharField()
    scope = serializers.CharField()
    summary = serializers.DictField()
    checks = serializers.ListField(child=serializers.DictField())
    api_surface = serializers.ListField(child=serializers.DictField())
    frontend_surface = serializers.ListField(child=serializers.DictField())
    environment_flags = serializers.ListField(child=serializers.DictField())
    smoke_commands = serializers.ListField(child=serializers.DictField(), required=False)
    management_commands = serializers.ListField(child=serializers.DictField(), required=False)
    recommendations = serializers.ListField(child=serializers.DictField(), required=False)



class AdminCommerceReadinessQuerySerializer(serializers.Serializer):
    include_commands = serializers.BooleanField(required=False, default=True)
    include_frontend = serializers.BooleanField(required=False, default=True)
    include_recommendations = serializers.BooleanField(required=False, default=True)


class AdminCommerceReadinessSerializer(serializers.Serializer):
    status = serializers.CharField()
    generated_at = serializers.DateTimeField()
    version = serializers.CharField()
    scope = serializers.CharField()
    summary = serializers.DictField()
    checks = serializers.ListField(child=serializers.DictField())
    api_surface = serializers.ListField(child=serializers.DictField())
    frontend_surface = serializers.ListField(child=serializers.DictField(), required=False)
    smoke_commands = serializers.ListField(child=serializers.DictField(), required=False)
    management_commands = serializers.ListField(child=serializers.DictField(), required=False)
    recommendations = serializers.ListField(child=serializers.DictField(), required=False)


class AdminProductionReadinessQuerySerializer(serializers.Serializer):
    include_commands = serializers.BooleanField(required=False, default=True)
    include_recommendations = serializers.BooleanField(required=False, default=True)


class AdminProductionReadinessSerializer(serializers.Serializer):
    status = serializers.CharField()
    generated_at = serializers.DateTimeField()
    version = serializers.CharField()
    scope = serializers.CharField()
    summary = serializers.DictField()
    checks = serializers.ListField(child=serializers.DictField())
    api_surface = serializers.ListField(child=serializers.DictField())
    frontend_surface = serializers.ListField(child=serializers.DictField())
    seed_data = serializers.ListField(child=serializers.DictField())
    smoke_commands = serializers.ListField(child=serializers.DictField(), required=False)
    management_commands = serializers.ListField(child=serializers.DictField(), required=False)
    recommendations = serializers.ListField(child=serializers.DictField(), required=False)
