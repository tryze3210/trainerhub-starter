import { PageHeader } from '@/components/page-header';
import { StoreGrid } from '@/components/store-grid';
import { getStoreVideos } from '@/lib/api';
import { PurchaseButton } from '../purchase-button';

export default async function StoreVideosPage() {
  const items = await getStoreVideos();
  return (
    <div className="space-y-6">
      <PageHeader title="Video store" description="One-time purchases connected to orders + checkout API." />
      <StoreGrid items={items} actionLabel="Buy" renderAction={(item) => <PurchaseButton itemType="video" itemId={item.id} />} />
    </div>
  );
}
