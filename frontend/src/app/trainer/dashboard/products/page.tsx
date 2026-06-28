import { TrainerDashboardShell } from '@/modules/trainer-dashboard/components/trainer-dashboard-shell';
import { TrainerProductBuilderDashboard } from '@/modules/trainer-products/components/trainer-product-builder-dashboard';

export default function TrainerProductsPage() {
  return (
    <TrainerDashboardShell
      title="Продукты"
      description="Создавайте, проверяйте и публикуйте платные продукты тренера."
    >
      <TrainerProductBuilderDashboard />
    </TrainerDashboardShell>
  );
}
