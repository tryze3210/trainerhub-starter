import { getCheckoutSessions, getMyPayments } from '@/lib/api';
import { PageHeader } from '@/components/page-header';

export default async function BillingHistoryPage() {
  const [checkouts, payments] = await Promise.all([getCheckoutSessions(), getMyPayments()]);

  return (
    <div className="space-y-6">
      <PageHeader title="Billing history" description="User-visible billing timeline for support and reconciliation." />
      <div className="space-y-3">
        {checkouts.map((checkout) => (
          <div key={checkout.id} className="rounded-xl border p-4">
            <div>Checkout #{checkout.id}</div>
            <div>{checkout.checkout_type} → target {checkout.target_id}</div>
            <div>Status: {checkout.status}</div>
          </div>
        ))}
        {payments.map((payment) => (
          <div key={`payment-${payment.id}`} className="rounded-xl border p-4">
            <div>Payment #{payment.id}</div>
            <div>Status: {payment.status}</div>
            <div>Provider: {payment.provider}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
