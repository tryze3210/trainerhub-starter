import type { Metadata } from 'next';
import { TrainerDirectoryPage } from '@/modules/public-storefront/components/trainer-directory-page';

export const dynamic = 'force-dynamic';

export const metadata: Metadata = {
  title: 'Тренеры — TrainerHub',
  description: 'Публичная витрина тренеров с профилями, специализациями и активными продуктами.',
};

export default function TrainersPage() {
  return <TrainerDirectoryPage />;
}
