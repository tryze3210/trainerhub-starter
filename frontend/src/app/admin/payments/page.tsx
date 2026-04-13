import { getAdminPayments } from '@/lib/api';
import { PageHeader } from '@/components/page-header';
import { RefundPaymentButton } from './payment-actions';

export default async function AdminPaymentsPage() {
  const items = await getAdminPayments();

  return (
    <div className="space-y-6">
      <PageHeader title="Admin payments" description="Finance operations view for reconciliation and manual actions." />
      <div className="space-y-3">
        {items.map((item: any) => (
          <div key={item.id} className="rounded-xl border p-4">
            <div>Payment {item.id}</div>
            <div>Status: {item.status}</div>
            <div>Gross: {item.gross_amount}</div>
            <div>Fee: {item.platform_fee}</div>
            <div>Trainer net: {item.trainer_amount}</div>
            <RefundPaymentButton id={item.id} />
          </div>
        ))}
      </div>
    </div>
  );
}
