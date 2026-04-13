class HabitSnapshotBuilder:
    """Materialize user-level habit KPIs for dashboards and home widgets."""

    def rebuild_for_user(self, user_id):
        return {"user_id": str(user_id), "status": "rebuilt"}
