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
    title: `Программа ${slug} — TrainerHub`,
    description: 'Страница программы тренировок с описанием, ценой, тренером и доступом после оплаты.',
  };
}

export default async function ProgramDetailPage({ params }: Props) {
  const { slug } = await params;
  return <ContentDetailPage type="program" slug={slug} />;
}
