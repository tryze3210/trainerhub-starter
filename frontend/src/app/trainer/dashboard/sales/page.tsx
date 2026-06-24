'use client';

import { TrainerDashboardShell } from '@/modules/trainer-dashboard/components/trainer-dashboard-shell';
import { TrainerSalesDashboard } from '@/modules/trainer-sales/components/trainer-sales-dashboard';

export default function TrainerSalesPage() {
  return (
    <TrainerDashboardShell
      title="Sales dashboard"
      description="Продажи, выручка, refunds, conversion и доступы учеников в одном операционном экране."
    >
      <TrainerSalesDashboard />
    </TrainerDashboardShell>
  );
}
