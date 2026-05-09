import type { Metadata } from 'next';
import { MarketplaceCatalogPage } from '@/modules/public-storefront/components/marketplace-catalog-page';

export const dynamic = 'force-dynamic';

export const metadata: Metadata = {
  title: 'Каталог тренировок — TrainerHub',
  description: 'Публичный marketplace-каталог видео, программ и bundle-предложений тренеров.',
};

export default function CatalogPage() {
  return <MarketplaceCatalogPage />;
}
