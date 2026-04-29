'use client';

import { ProtectedPage } from '@/components/protected-page';
import { TrainerDashboardShell } from '@/modules/trainer-dashboard/components/trainer-dashboard-shell';
import { TrainerOnboardingChecklist } from '@/modules/trainer-onboarding/components/trainer-onboarding-checklist';

export default function TrainerOnboardingPage() {
  return (
    <ProtectedPage title="Trainer onboarding" description="Onboarding тренера доступен только после авторизации.">
      <TrainerDashboardShell
        title="Trainer application & onboarding"
        description="Собери профиль, оформи заявку на модерацию и закрой ключевые шаги, чтобы перейти к публикации контента."
      >
        <TrainerOnboardingChecklist />
      </TrainerDashboardShell>
    </ProtectedPage>
  );
}
