from rest_framework import serializers


class HabitPlanSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    title = serializers.CharField()
    category = serializers.CharField()
    cadence = serializers.CharField()
    target_value = serializers.DecimalField(max_digits=10, decimal_places=2)
    unit = serializers.CharField()


class DailyCheckInCreateSerializer(serializers.Serializer):
    habit_plan_id = serializers.UUIDField()
    checkin_date = serializers.DateField()
    value = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    note = serializers.CharField(required=False, allow_blank=True)


class JournalEntrySerializer(serializers.Serializer):
    entry_date = serializers.DateField()
    mood = serializers.CharField(required=False, allow_blank=True)
    energy = serializers.IntegerField(required=False)
    body = serializers.CharField()
