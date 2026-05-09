from __future__ import annotations

from rest_framework import serializers


class AdminReconciliationRepairSerializer(serializers.Serializer):
    ACTION_CHOICES = (
        ('retry_outbox', 'Retry outbox message'),
        ('mark_outbox_dead', 'Mark outbox message as dead'),
        ('reprocess_webhook', 'Reprocess payment webhook'),
        ('grant_order_access', 'Grant missing order access'),
        ('revoke_entitlement', 'Revoke entitlement'),
        ('project_payout_accrual', 'Project payout accrual'),
        ('reverse_payout_accrual', 'Reverse payout accrual'),
    )
    ENTITY_CHOICES = (
        ('outbox_message', 'Outbox message'),
        ('payment_webhook', 'Payment webhook'),
        ('payment', 'Payment'),
        ('order', 'Order'),
        ('entitlement', 'Entitlement'),
        ('payout_ledger', 'Payout ledger'),
    )

    action = serializers.ChoiceField(choices=ACTION_CHOICES)
    entity_type = serializers.ChoiceField(choices=ENTITY_CHOICES)
    entity_id = serializers.CharField(max_length=128)
    reason = serializers.CharField(max_length=1000)
    force = serializers.BooleanField(required=False, default=False)
    dry_run = serializers.BooleanField(required=False, default=False)
    confirm_token = serializers.CharField(required=False, allow_blank=True, max_length=64)


class AdminReconciliationRepairPolicySerializer(serializers.Serializer):
    ACTION_CHOICES = AdminReconciliationRepairSerializer.ACTION_CHOICES
    ENTITY_CHOICES = (('', 'Any'),) + AdminReconciliationRepairSerializer.ENTITY_CHOICES

    action = serializers.ChoiceField(choices=ACTION_CHOICES)
    entity_type = serializers.ChoiceField(required=False, allow_blank=True, choices=ENTITY_CHOICES, default='')
    entity_id = serializers.CharField(required=False, allow_blank=True, max_length=128, default='')
    force = serializers.BooleanField(required=False, default=False)


class AdminReconciliationRepairResultSerializer(serializers.Serializer):
    action = serializers.CharField()
    status = serializers.CharField()
    entity_type = serializers.CharField()
    entity_id = serializers.CharField()
    message = serializers.CharField()
    changed = serializers.BooleanField()
    result = serializers.DictField()
    audit_event_id = serializers.CharField(required=False, allow_blank=True)
    audit_event_href = serializers.CharField(required=False, allow_blank=True)
    entity_href = serializers.CharField(required=False, allow_blank=True)
    reconciliation_href = serializers.CharField(required=False, allow_blank=True)
    audit = serializers.DictField(required=False)

    repair_policy = serializers.DictField(required=False)
    workflow = serializers.DictField(required=False)

    reconciliation_snapshot_id = serializers.CharField(required=False, allow_blank=True)
    reconciliation_snapshot_href = serializers.CharField(required=False, allow_blank=True)
    reconciliation_snapshot_source = serializers.CharField(required=False, allow_blank=True)
    previous_problem_count = serializers.IntegerField(required=False, allow_null=True)
    current_problem_count = serializers.IntegerField(required=False, allow_null=True)
    problem_delta = serializers.IntegerField(required=False, allow_null=True)
    improved = serializers.BooleanField(required=False)
    repair_snapshot = serializers.DictField(required=False)
