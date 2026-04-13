import { PageHeader } from '@/components/page-header';
import { getMyInvoices } from '@/lib/api';

export default async function InvoicesPage() {
  const invoices = await getMyInvoices();
  return (
    <div className="space-y-6">
      <PageHeader title="Invoices and receipts" description="Document layer generated after paid orders." />
      <div className="space-y-3">
        {invoices.map((invoice) => (
          <div key={invoice.id} className="rounded-2xl border p-4">
            <div className="font-semibold">{invoice.document_number}</div>
            <div className="text-sm text-gray-600">{invoice.document_type}</div>
            <div className="text-sm">{invoice.gross_amount} {invoice.currency}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
