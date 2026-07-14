import { TrainerDashboardShell } from '@/modules/trainer-dashboard/components/trainer-dashboard-shell';
import { TrainerRevenueDashboard } from '@/modules/trainer-revenue/components/trainer-revenue-dashboard';

export default function TrainerRevenuePage() {
  return (
    <TrainerDashboardShell
      title="Финансы"
      description="Баланс, комиссии, выплаты и движение средств."
    >
      <TrainerRevenueDashboard />
    </TrainerDashboardShell>
  );
}
