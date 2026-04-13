from decimal import Decimal


class DailyCheckInService:
    """Integration seam. Wire to real ORM repositories/application services."""

    def submit_checkin(self, habit_plan, date_value, value=Decimal("1"), note=""):
        return {
            "habit_plan_id": str(habit_plan.id),
            "checkin_date": str(date_value),
            "value": str(value),
            "note": note,
            "status": "completed",
        }
