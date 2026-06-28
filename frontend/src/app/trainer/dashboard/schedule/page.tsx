'use client';

import { TrainerBookingDashboard } from '@/modules/trainer-booking/components/trainer-booking-dashboard';
import { TrainerDashboardShell } from '@/modules/trainer-dashboard/components/trainer-dashboard-shell';

export default function TrainerSchedulePage() {
  return (
    <TrainerDashboardShell
      title="Расписание"
      description="Настраивайте рабочие часы, создавайте слоты и ведите посещаемость."
    >
      <TrainerBookingDashboard />
    </TrainerDashboardShell>
  );
}
