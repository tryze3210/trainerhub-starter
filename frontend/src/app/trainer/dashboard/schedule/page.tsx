'use client';

import { TrainerBookingDashboard } from '@/modules/trainer-booking/components/trainer-booking-dashboard';
import { TrainerDashboardShell } from '@/modules/trainer-dashboard/components/trainer-dashboard-shell';

export default function TrainerSchedulePage() {
  return (
    <TrainerDashboardShell
      title="Расписание"
      description="Расписание, запись на занятия, лимиты мест, отмены и лист ожидания."
    >
      <TrainerBookingDashboard />
    </TrainerDashboardShell>
  );
}
