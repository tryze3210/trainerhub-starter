import { Suspense } from 'react';
import { TrainerDashboardShell } from '@/modules/trainer-dashboard/components/trainer-dashboard-shell';
import { TrainerProductBuilderDashboard } from '@/modules/trainer-products/components/trainer-product-builder-dashboard';

export default function TrainerProductsPage() {
  return (
    <TrainerDashboardShell
      title="Продукты"
      description="Создавайте платные видео, наборы и программы, настраивайте цену, доступ и публикацию для каталога TrainerHub."
    >
      <Suspense fallback={<div className="trainer-content-loading">Загрузка конструктора продуктов...</div>}>
        <TrainerProductBuilderDashboard />
      </Suspense>
    </TrainerDashboardShell>
  );
}
