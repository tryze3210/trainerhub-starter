from __future__ import annotations

from rest_framework import serializers

from apps.entitlements.models import EntitlementTargetType


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


class AdminGlobalSearchQuerySerializer(serializers.Serializer):
    q = serializers.CharField(required=False, allow_blank=True, max_length=255, default="")
    categories = serializers.CharField(required=False, allow_blank=True, max_length=255, default="")
    limit = serializers.IntegerField(required=False, min_value=1, max_value=25, default=10)


class AdminGlobalSearchSerializer(serializers.Serializer):
    query = serializers.CharField(allow_blank=True)
    categories = serializers.ListField(child=serializers.CharField())
    limit = serializers.IntegerField()
    generated_at = serializers.DateTimeField()
    total_count = serializers.IntegerField()
    results = serializers.ListField(child=serializers.DictField())
    results_by_category = serializers.DictField()


class SupportConsoleQuerySerializer(serializers.Serializer):
    user_id = serializers.CharField(required=False, allow_blank=True, max_length=64, default="")
    email = serializers.EmailField(required=False, allow_blank=True, default="")
    limit = serializers.IntegerField(required=False, min_value=1, max_value=100, default=25)


class SupportConsoleSnapshotSerializer(serializers.Serializer):
    user = serializers.DictField()
    orders = serializers.ListField(child=serializers.DictField())
    payments = serializers.ListField(child=serializers.DictField())
    entitlements = serializers.ListField(child=serializers.DictField())
    webhook_errors = serializers.ListField(child=serializers.DictField())
    notification_deliveries = serializers.ListField(child=serializers.DictField())
    summary = serializers.DictField()
    generated_at = serializers.DateTimeField()


class SupportNotificationResendSerializer(serializers.Serializer):
    delivery_id = serializers.UUIDField()
    reason = serializers.CharField(required=False, allow_blank=True, max_length=500, default="support_console_resend")


class SupportEntitlementFixSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=[("grant", "Grant"), ("revoke", "Revoke")])
    reason = serializers.CharField(max_length=500)
    user_id = serializers.CharField(required=False, allow_blank=True, max_length=64, default="")
    email = serializers.EmailField(required=False, allow_blank=True, default="")
    entitlement_id = serializers.CharField(required=False, allow_blank=True, max_length=64, default="")
    target_type = serializers.ChoiceField(
        choices=EntitlementTargetType.choices,
        required=False,
        allow_blank=True,
        default="",
    )
    target_id = serializers.CharField(required=False, allow_blank=True, max_length=64, default="")

    def validate(self, attrs):
        action = attrs.get("action")
        if action == "grant":
            if not (attrs.get("user_id") or attrs.get("email")):
                raise serializers.ValidationError({"user": "user_id or email is required for grants."})
            if not attrs.get("target_type"):
                raise serializers.ValidationError({"target_type": "target_type is required for grants."})
            if not attrs.get("target_id"):
                raise serializers.ValidationError({"target_id": "target_id is required for grants."})
        if action == "revoke" and not attrs.get("entitlement_id"):
            if not (attrs.get("user_id") or attrs.get("email")):
                raise serializers.ValidationError({"user": "user_id/email or entitlement_id is required for revoke."})
            if not attrs.get("target_type"):
                raise serializers.ValidationError({"target_type": "target_type is required when entitlement_id is omitted."})
            if not attrs.get("target_id"):
                raise serializers.ValidationError({"target_id": "target_id is required when entitlement_id is omitted."})
        return attrs


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
    role_matrix = serializers.ListField(child=serializers.DictField(), required=False)
    ci_gate = serializers.DictField(required=False)
    launch_candidate = serializers.DictField(required=False)
    production_launch_pack = serializers.DictField(required=False)
    smoke_commands = serializers.ListField(child=serializers.DictField(), required=False)
    management_commands = serializers.ListField(child=serializers.DictField(), required=False)
    recommendations = serializers.ListField(child=serializers.DictField(), required=False)


class AdminLaunchCandidateQuerySerializer(serializers.Serializer):
    include_artifacts = serializers.BooleanField(required=False, default=True)


class AdminLaunchCandidateSerializer(serializers.Serializer):
    status = serializers.CharField()
    version = serializers.CharField()
    project_version = serializers.CharField()
    generated_at = serializers.DateTimeField()
    scope = serializers.CharField()
    release_notes = serializers.ListField(child=serializers.DictField())
    smoke_checklist = serializers.ListField(child=serializers.DictField())
    production_env_checklist = serializers.ListField(child=serializers.DictField())
    known_limitations = serializers.ListField(child=serializers.DictField())
    required_artifacts = serializers.ListField(child=serializers.DictField(), required=False)
    missing_artifacts = serializers.ListField(child=serializers.CharField())
    release_decision = serializers.DictField()


class AdminProductionLaunchPackQuerySerializer(serializers.Serializer):
    include_content = serializers.BooleanField(required=False, default=False)


class AdminProductionLaunchPackSerializer(serializers.Serializer):
    status = serializers.CharField()
    version = serializers.CharField()
    project_version = serializers.CharField(allow_blank=True)
    generated_at = serializers.DateTimeField()
    scope = serializers.CharField()
    documents = serializers.ListField(child=serializers.DictField())
    missing_documents = serializers.ListField(child=serializers.CharField())
    final_gates = serializers.ListField(child=serializers.DictField())
    handoffs = serializers.ListField(child=serializers.DictField())
    release_state = serializers.DictField()


class AdminOpsRunbookQuerySerializer(serializers.Serializer):
    include_content = serializers.BooleanField(required=False, default=False)


class AdminOpsRunbookIndexSerializer(serializers.Serializer):
    status = serializers.CharField()
    total = serializers.IntegerField()
    missing = serializers.ListField(child=serializers.CharField())
    runbooks = serializers.ListField(child=serializers.DictField())


class AdminOpsRunbookDetailSerializer(serializers.Serializer):
    key = serializers.CharField()
    title = serializers.CharField()
    incident_type = serializers.CharField()
    severity = serializers.CharField()
    path = serializers.CharField()
    exists = serializers.BooleanField()
    sections = serializers.ListField(child=serializers.CharField(), required=False)
    content = serializers.CharField(required=False, allow_blank=True)
