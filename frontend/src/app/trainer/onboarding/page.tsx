'use client';

import { ProtectedPage } from '@/components/protected-page';
import { TrainerDashboardShell } from '@/modules/trainer-dashboard/components/trainer-dashboard-shell';
import { TrainerOnboardingChecklist } from '@/modules/trainer-onboarding/components/trainer-onboarding-checklist';

export default function TrainerOnboardingPage() {
  return (
    <ProtectedPage
      title="Trainer onboarding"
      description="Заявка тренера, модерация, выдача trainer role и разблокировка dashboard."
    >
      <TrainerDashboardShell
        title="Trainer onboarding"
        description="Заполни заявку, отправь её на admin review и отслеживай готовность к публикации продуктов."
      >
        <TrainerOnboardingChecklist />
      </TrainerDashboardShell>
    </ProtectedPage>
  );
}
