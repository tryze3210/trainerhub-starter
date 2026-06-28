'use client';

import { ProtectedPage } from '@/components/protected-page';
import { TrainerDashboardShell } from '@/modules/trainer-dashboard/components/trainer-dashboard-shell';
import { TrainerOnboardingChecklist } from '@/modules/trainer-onboarding/components/trainer-onboarding-checklist';

export default function TrainerOnboardingPage() {
  return (
    <ProtectedPage
      title="Профиль тренера"
      description="Профиль тренера доступен только после входа."
    >
      <TrainerDashboardShell
        title="Профиль тренера"
        description="Заполните публичный профиль, чтобы ученики понимали вашу специализацию и могли покупать продукты."
      >
        <TrainerOnboardingChecklist />
      </TrainerDashboardShell>
    </ProtectedPage>
  );
}
