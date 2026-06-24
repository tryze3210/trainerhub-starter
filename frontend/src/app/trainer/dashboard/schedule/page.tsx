'use client';

import { TrainerBookingDashboard } from '@/modules/trainer-booking/components/trainer-booking-dashboard';
import { TrainerDashboardShell } from '@/modules/trainer-dashboard/components/trainer-dashboard-shell';

export default function TrainerSchedulePage() {
  return (
    <TrainerDashboardShell
      title="Booking schedule"
      description="Расписание, запись на занятия, лимиты мест, отмены и waitlist."
    >
      <TrainerBookingDashboard />
    </TrainerDashboardShell>
  );
}
