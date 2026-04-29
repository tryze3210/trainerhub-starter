'use client';

import { ProtectedPage } from '@/components/protected-page';
import { TrainerDashboardShell } from '@/modules/trainer-dashboard/components/trainer-dashboard-shell';
import { TrainerUploadPanel } from '@/modules/upload/components/trainer-upload-panel';

export default function TrainerVideosPage() {
  return (
    <ProtectedPage title="Trainer content studio" description="Контентная студия тренера доступна только после авторизации.">
      <TrainerDashboardShell
        title="Content studio / video · program · bundle editor"
        description="Теперь это уже не просто upload flow, а контур draft → reorder → lessons/composition → publish → storefront reviews/checkout."
      >
        <TrainerUploadPanel />
      </TrainerDashboardShell>
    </ProtectedPage>
  );
}
