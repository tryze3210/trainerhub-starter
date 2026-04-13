import { getMyPayoutBalance, getMyPayoutRequests } from '@/lib/api';
import { PageHeader } from '@/components/page-header';
import { RequestPayoutButton } from './payout-actions';

export default async function TrainerPayoutsPage() {
  const [balance, payouts] = await Promise.all([getMyPayoutBalance(), getMyPayoutRequests()]);

  return (
    <div className="space-y-6">
      <PageHeader title="Trainer payouts" description="Available balance, reserved balance, and payout requests." />
      <div className="rounded-xl border p-4">
        <div>Available: {balance.available_amount} {balance.currency}</div>
        <div>Reserved: {balance.reserved_amount} {balance.currency}</div>
        <div>Lifetime earned: {balance.lifetime_earned_amount} {balance.currency}</div>
        <RequestPayoutButton />
      </div>
      <div className="space-y-3">
        {payouts.map((payout) => (
          <div key={payout.id} className="rounded-xl border p-4">
            <div>Payout #{payout.id}</div>
            <div>Status: {payout.status}</div>
            <div>Amount: {payout.amount} {payout.currency}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
