import type { Metadata } from 'next';

import { ProtectedPage } from '@/components/protected-page';
import { AdminPaymentOperationsDashboard } from '@/modules/admin-payments/components/admin-payment-operations-dashboard';

export const metadata: Metadata = {
  title: 'Платежи администратора · TrainerHub',
  description: 'Операции с платежами: платежи, вебхуки, возвраты, доступы и проблемы сверки.',
};

export default function AdminPaymentsPage() {
  return (
    <ProtectedPage
      title="Платежи администратора"
      description="Операционный центр платежей: платежи, вебхуки, возвраты, статусы доступов и сверка."
    >
      <AdminPaymentOperationsDashboard />
    </ProtectedPage>
  );
}
