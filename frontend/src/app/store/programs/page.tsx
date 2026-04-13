import { PageHeader } from '@/components/page-header';
import { StoreGrid } from '@/components/store-grid';
import { getStorePrograms } from '@/lib/api';
import { PurchaseButton } from '../purchase-button';

export default async function StoreProgramsPage() {
  const items = await getStorePrograms();
  return (
    <div className="space-y-6">
      <PageHeader title="Program store" description="Paid programs through central orders domain." />
      <StoreGrid items={items} actionLabel="Buy" renderAction={(item) => <PurchaseButton itemType="program" itemId={item.id} />} />
    </div>
  );
}
