import type { Metadata } from 'next';

import { ProtectedPage } from '@/components/protected-page';
import { AdminPaymentOperationsDashboard } from '@/modules/admin-payments/components/admin-payment-operations-dashboard';

export const metadata: Metadata = {
  title: 'Admin payments · TrainerHub',
  description: 'Payment operations: payments, webhook events, refunds, entitlements and reconciliation issues.',
};

export default function AdminPaymentsPage() {
  return (
    <ProtectedPage
      title="Admin payments"
      description="Операционный центр платежей: payments, webhooks, refunds, entitlement status и reconciliation."
    >
      <AdminPaymentOperationsDashboard />
    </ProtectedPage>
  );
}
