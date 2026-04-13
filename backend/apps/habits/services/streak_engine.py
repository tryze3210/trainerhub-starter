from datetime import timedelta


class StreakEngine:
    @staticmethod
    def recalculate(state, checkin_date):
        if state.last_checkin_date is None:
            state.current_streak = 1
        elif checkin_date == state.last_checkin_date:
            return state
        elif checkin_date == state.last_checkin_date + timedelta(days=1):
            state.current_streak += 1
        else:
            state.current_streak = 1
        state.longest_streak = max(state.longest_streak, state.current_streak)
        state.last_checkin_date = checkin_date
        return state
