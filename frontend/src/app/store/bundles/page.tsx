import { PageHeader } from '@/components/page-header';
import { StoreGrid } from '@/components/store-grid';
import { getStoreBundles } from '@/lib/api';
import { PurchaseButton } from '../purchase-button';

export default async function StoreBundlesPage() {
  const items = await getStoreBundles();
  return (
    <div className="space-y-6">
      <PageHeader title="Bundle store" description="Bundles create both bundle entitlement and nested access grants." />
      <StoreGrid items={items} actionLabel="Buy" renderAction={(item) => <PurchaseButton itemType="bundle" itemId={item.id} />} />
    </div>
  );
}
