from rest_framework import serializers


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
