import type { Metadata } from 'next';
import { ContentDetailPage } from '@/modules/public-storefront/components/content-detail-page';

type PageParams = Promise<{ slug: string }>;

type Props = {
  params: PageParams;
};

export const dynamic = 'force-dynamic';

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  return {
    title: `Bundle ${slug} — TrainerHub`,
    description: 'Публичная карточка bundle-предложения с ценой, тренером и CTA на покупку.',
  };
}

export default async function BundleDetailPage({ params }: Props) {
  const { slug } = await params;
  return <ContentDetailPage type="bundle" slug={slug} />;
}
