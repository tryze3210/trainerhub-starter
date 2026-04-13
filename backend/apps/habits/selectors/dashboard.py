class HabitDashboardSelector:
    def get_user_dashboard(self, user_id):
        return {
            "user_id": str(user_id),
            "active_habits": 0,
            "completion_rate_7d": "0.00",
            "journal_entries": 0,
        }
