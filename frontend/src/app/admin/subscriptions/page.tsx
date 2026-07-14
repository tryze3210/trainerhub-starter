import type { Metadata } from 'next';
import { ProtectedPage } from '@/components/protected-page';
import { AdminSubscriptionOperationsDashboard } from '@/modules/admin-subscriptions/components/admin-subscription-operations-dashboard';

export const metadata: Metadata = {
  title: 'Admin subscriptions | TrainerHub',
  description: 'Subscription lifecycle operations, entitlement sync, expire-due and reconciliation controls.',
};

export default function AdminПодпискиPage() {
  return (
    <ProtectedPage
      title="Подписки администратора"
      description="Операции жизненного цикла подписок, синхронизация доступов и контроль регулярной выручки."
    >
      <AdminSubscriptionOperationsDashboard />
    </ProtectedPage>
  );
}
