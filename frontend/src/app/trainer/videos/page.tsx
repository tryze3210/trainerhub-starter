'use client';

import Link from 'next/link';
import { ProtectedPage } from '@/components/protected-page';
import { TrainerDashboardShell } from '@/modules/trainer-dashboard/components/trainer-dashboard-shell';
import { TrainerDashboardCard } from '@/modules/trainer-cabinet/components';
import { TrainerUploadPanel } from '@/modules/upload/components/trainer-upload-panel';

export default function TrainerVideosPage() {
  return (
    <ProtectedPage title="Видео и материалы" description="Контентная студия тренера доступна только после авторизации.">
      <TrainerDashboardShell
        title="Видео и материалы"
        description="Загружайте видеоуроки, готовьте материалы и собирайте основу для программ и платных продуктов."
      >
        <div className="trainer-upload-context">
          <TrainerDashboardCard title="Загрузка материалов" description="Видео останется в библиотеке тренера. После публикации его можно использовать в программах и продуктах.">
            <TrainerUploadPanel />
          </TrainerDashboardCard>
          <TrainerDashboardCard title="Требования к видео">
            <div className="trainer-product-list">
              <div className="trainer-section-card">Проверяйте название, описание и доступ перед продажей.</div>
              <div className="trainer-section-card">После загрузки дождитесь обработки файла.</div>
              <div className="trainer-section-card">Перед публикацией убедитесь, что материал подходит для платного продукта.</div>
            </div>
          </TrainerDashboardCard>
          <TrainerDashboardCard title="Быстрые ссылки">
            <div className="trainer-page-actions">
              <Link href="/trainer/dashboard/products" className="premium-primary-button">Создать продукт</Link>
              <Link href="/catalog" className="premium-secondary-button">Открыть каталог</Link>
              <Link href="/trainer/dashboard/analytics" className="premium-secondary-button">Перейти к аналитике</Link>
            </div>
          </TrainerDashboardCard>
        </div>
      </TrainerDashboardShell>
    </ProtectedPage>
  );
}
