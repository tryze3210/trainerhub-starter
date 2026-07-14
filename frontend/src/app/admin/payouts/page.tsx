import type { Metadata } from 'next';

import { ProtectedPage } from '@/components/protected-page';
import { AdminPayoutOperationsDashboard } from '@/modules/admin-payouts/components/admin-payout-operations-dashboard';

export const metadata: Metadata = {
  title: 'Admin payouts · TrainerHub',
  description: 'Admin payout operations: requests, transitions, risk holds, projection and reconciliation.',
};

export default function AdminВыплатыPage() {
  return (
    <ProtectedPage
      title="Выплаты администратора"
      description="Операционный центр выплат: одобрение, обработка, отметка оплаты, отклонение, риск-холды и сверка."
    >
      <AdminPayoutOperationsDashboard />
    </ProtectedPage>
  );
}
