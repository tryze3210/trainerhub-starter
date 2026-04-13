from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, time
from zoneinfo import ZoneInfo

from django.db import transaction

from apps.booking.models import AvailabilityRule, BookingProfile, BookingSlot


@dataclass
class SlotGenerationResult:
    created: int
    existing: int


class SlotGenerationService:
    def __init__(self, trainer):
        self.trainer = trainer
        self.profile = BookingProfile.objects.get(trainer=trainer)
        self.tz = ZoneInfo(self.profile.timezone)

    @transaction.atomic
    def generate_range(self, start_date, end_date) -> SlotGenerationResult:
        created = 0
        existing = 0
        rules = AvailabilityRule.objects.filter(trainer=self.trainer, is_active=True)
        cursor = start_date
        while cursor <= end_date:
            weekday_rules = rules.filter(weekday=cursor.weekday())
            for rule in weekday_rules:
                start_dt = datetime.combine(cursor, time.min, tzinfo=self.tz) + timedelta(minutes=rule.start_minute)
                end_dt = datetime.combine(cursor, time.min, tzinfo=self.tz) + timedelta(minutes=rule.end_minute)
                step = timedelta(minutes=rule.slot_size_minutes)
                current = start_dt
                while current + step <= end_dt:
                    _, was_created = BookingSlot.objects.get_or_create(
                        trainer=self.trainer,
                        starts_at=current,
                        defaults={
                            "ends_at": current + step,
                            "status": BookingSlot.STATUS_OPEN,
                            "source": "availability_rule",
                        },
                    )
                    if was_created:
                        created += 1
                    else:
                        existing += 1
                    current += step
            cursor += timedelta(days=1)
        return SlotGenerationResult(created=created, existing=existing)
