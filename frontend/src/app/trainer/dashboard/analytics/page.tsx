import { TrainerContentAnalyticsDashboard } from '@/modules/trainer-analytics/components/trainer-content-analytics-dashboard';
import { TrainerDashboardShell } from '@/modules/trainer-dashboard/components/trainer-dashboard-shell';

export default function TrainerAnalyticsPage() {
  return (
    <TrainerDashboardShell
      title="Analytics"
      description="Контентная аналитика тренера: просмотры, покупки, конверсия и выручка."
    >
      <TrainerContentAnalyticsDashboard />
    </TrainerDashboardShell>
  );
}
