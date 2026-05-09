import { TrainerDashboardShell } from '@/modules/trainer-dashboard/components/trainer-dashboard-shell';
import { TrainerProductBuilderDashboard } from '@/modules/trainer-products/components/trainer-product-builder-dashboard';

export default function TrainerProductsPage() {
  return (
    <TrainerDashboardShell
      title="Product builder"
      description="Create, validate, publish and archive paid trainer products and video bundles."
    >
      <TrainerProductBuilderDashboard />
    </TrainerDashboardShell>
  );
}
