import { TrainerDashboardShell } from '@/modules/trainer-dashboard/components/trainer-dashboard-shell';
import { TrainerSalesDashboard } from '@/modules/trainer-sales/components/trainer-sales-dashboard';

export default function TrainerSalesPage() {
  return (
    <TrainerDashboardShell
      title="Продажи"
      description="Продажи, выручка, возвраты, конверсия и доступы учеников в одном операционном экране."
    >
      <TrainerSalesDashboard />
    </TrainerDashboardShell>
  );
}
