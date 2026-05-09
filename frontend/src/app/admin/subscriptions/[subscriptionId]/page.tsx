import type { Metadata } from 'next';
import { ProtectedPage } from '@/components/protected-page';
import { AdminSubscriptionDetailPage } from '@/modules/admin-subscriptions/components/admin-subscription-detail-page';

export const metadata: Metadata = {
  title: 'Admin subscription detail | TrainerHub',
  description: 'Subscription lifecycle detail, renewal projection and entitlement sync controls.',
};

export default async function AdminSubscriptionDetailRoute({ params }: { params: Promise<{ subscriptionId: string }> }) {
  const { subscriptionId } = await params;

  return (
    <ProtectedPage
      title="Admin subscription detail"
      description="Подробная lifecycle-карточка подписки и ручные операции доступа."
    >
      <AdminSubscriptionDetailPage subscriptionId={subscriptionId} />
    </ProtectedPage>
  );
}
