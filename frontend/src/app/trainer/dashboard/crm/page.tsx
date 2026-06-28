'use client';

import { TrainerCRMDashboard } from '@/modules/trainer-crm/components/trainer-crm-dashboard';
import { TrainerDashboardShell } from '@/modules/trainer-dashboard/components/trainer-dashboard-shell';

export default function TrainerCRMPage() {
  return (
    <TrainerDashboardShell
      title="Ученики"
      description="Карточки клиентов, покупки, посещения, доступы, заметки тренера и сегменты."
    >
      <TrainerCRMDashboard />
    </TrainerDashboardShell>
  );
}
