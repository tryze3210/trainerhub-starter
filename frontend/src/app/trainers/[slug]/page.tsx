import type { Metadata } from 'next';
import { TrainerStorefrontPage } from '@/modules/public-storefront/components/trainer-storefront-page';

type PageParams = Promise<{ slug: string }>;

type Props = {
  params: PageParams;
};

export const dynamic = 'force-dynamic';

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  return {
    title: `Тренер ${slug} — TrainerHub`,
    description: 'Публичный storefront тренера: профиль, специализации, продукты и CTA на покупку.',
  };
}

export default async function TrainerStorefrontRoute({ params }: Props) {
  const { slug } = await params;
  return <TrainerStorefrontPage slug={slug} />;
}
