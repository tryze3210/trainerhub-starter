'use client';

import { TrainerDashboardShell } from '@/modules/trainer-dashboard/components/trainer-dashboard-shell';
import { TrainerPayoutRequestDashboard } from '@/modules/trainer-payouts/components/trainer-payout-request-dashboard';

export default function TrainerPayoutsPage() {
  return (
    <TrainerDashboardShell
      title="Payout requests"
      description="Создание заявок на выплату, резервирование баланса и отслеживание payout lifecycle."
    >
      <TrainerPayoutRequestDashboard />
    </TrainerDashboardShell>
  );
}
