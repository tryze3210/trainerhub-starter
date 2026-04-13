import { getMyPayments, getCheckoutSessions } from '@/lib/api';
import { PageHeader } from '@/components/page-header';

export default async function PaymentStatusPage() {
  const [payments, checkouts] = await Promise.all([getMyPayments(), getCheckoutSessions()]);

  return (
    <div className="space-y-6">
      <PageHeader title="Payment status" description="Checkout sessions and finalized payments." />
      <section className="space-y-3">
        <h2 className="text-lg font-semibold">Recent checkout sessions</h2>
        {checkouts.map((checkout) => (
          <div key={checkout.id} className="rounded-xl border p-4">
            <div>#{checkout.id} • {checkout.checkout_type}</div>
            <div>Status: {checkout.status}</div>
            <div>Amount: {checkout.gross_amount} {checkout.currency}</div>
          </div>
        ))}
      </section>
      <section className="space-y-3">
        <h2 className="text-lg font-semibold">Finalized payments</h2>
        {payments.map((payment) => (
          <div key={payment.id} className="rounded-xl border p-4">
            <div>Payment #{payment.id}</div>
            <div>Status: {payment.status}</div>
            <div>Gross: {payment.gross_amount} {payment.currency}</div>
            <div>Platform fee: {payment.platform_fee_amount}</div>
            <div>Trainer net: {payment.trainer_net_amount}</div>
          </div>
        ))}
      </section>
    </div>
  );
}
