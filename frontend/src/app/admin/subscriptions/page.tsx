import type { Metadata } from 'next';
import { ProtectedPage } from '@/components/protected-page';
import { AdminSubscriptionOperationsDashboard } from '@/modules/admin-subscriptions/components/admin-subscription-operations-dashboard';

export const metadata: Metadata = {
  title: 'Admin subscriptions | TrainerHub',
  description: 'Subscription lifecycle operations, entitlement sync, expire-due and reconciliation controls.',
};

export default function AdminSubscriptionsPage() {
  return (
    <ProtectedPage
      title="Admin subscriptions"
      description="Lifecycle operations для подписок, entitlement sync и recurring revenue контроля."
    >
      <AdminSubscriptionOperationsDashboard />
    </ProtectedPage>
  );
}
