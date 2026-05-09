'use client';

import { useParams } from 'next/navigation';

import { ProtectedPage } from '@/components/protected-page';
import { AdminPayoutDetailPage } from '@/modules/admin-payouts/components/admin-payout-detail-page';

export default function AdminPayoutDetailRoute() {
  const params = useParams<{ payoutId?: string }>();
  const payoutId = String(params?.payoutId || '');

  return (
    <ProtectedPage
      title="Payout detail"
      description="Детальная карточка payout request: lifecycle, ledger entries и ручные admin transitions."
    >
      <AdminPayoutDetailPage payoutId={payoutId} />
    </ProtectedPage>
  );
}
