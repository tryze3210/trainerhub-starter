import { getAdminPayouts } from '@/lib/api';
import { PageHeader } from '@/components/page-header';
import { PayoutApproveButton, PayoutProcessButton, PayoutPaidButton } from './payout-actions';

export default async function AdminPayoutsPage() {
  const items = await getAdminPayouts();

  return (
    <div className="space-y-6">
      <PageHeader title="Admin payouts" description="Approve, process and settle trainer payout requests." />
      <div className="space-y-3">
        {items.map((item: any) => (
          <div key={item.id} className="rounded-xl border p-4">
            <div>Payout {item.id}</div>
            <div>Trainer: {item.trainer_id}</div>
            <div>Status: {item.status}</div>
            <div>Amount: {item.amount} {item.currency}</div>
            <div>Destination: {item.destination_masked}</div>
            <div className="flex gap-2">
              <PayoutApproveButton id={item.id} />
              <PayoutProcessButton id={item.id} />
              <PayoutPaidButton id={item.id} />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
