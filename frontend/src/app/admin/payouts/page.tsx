import type { Metadata } from 'next';

import { ProtectedPage } from '@/components/protected-page';
import { AdminPayoutOperationsDashboard } from '@/modules/admin-payouts/components/admin-payout-operations-dashboard';

export const metadata: Metadata = {
  title: 'Admin payouts · TrainerHub',
  description: 'Admin payout operations: requests, transitions, risk holds, projection and reconciliation.',
};

export default function AdminPayoutsPage() {
  return (
    <ProtectedPage
      title="Admin payouts"
      description="Операционный центр выплат: approve, processing, mark-paid, reject, risk holds и reconciliation."
    >
      <AdminPayoutOperationsDashboard />
    </ProtectedPage>
  );
}
