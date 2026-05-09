'use client';

import { TrainerDashboardShell } from '@/modules/trainer-dashboard/components/trainer-dashboard-shell';
import { TrainerRevenueDashboard } from '@/modules/trainer-revenue/components/trainer-revenue-dashboard';

export default function TrainerRevenuePage() {
  return (
    <TrainerDashboardShell
      title="Revenue dashboard"
      description="Прозрачная витрина продаж, комиссии платформы, ledger-транзакций и payout-заявок."
    >
      <TrainerRevenueDashboard />
    </TrainerDashboardShell>
  );
}
