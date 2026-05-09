'use client';

import { ProtectedPage } from '@/components/protected-page';
import { AdminTrainerApplicationsDashboard } from '@/modules/admin-trainer-applications/components/admin-trainer-applications-dashboard';

export default function AdminTrainerApplicationsPage() {
  return (
    <ProtectedPage
      title="Trainer applications"
      description="Admin review queue: approve, reject, request changes и sync trainer access."
    >
      <main className="stack page-shell">
        <section className="hero card stack">
          <span className="eyebrow">Trainer onboarding ops</span>
          <h1>Trainer applications</h1>
          <p className="lead">
            Управляй заявками тренеров: approval сразу выдаёт trainer role, создаёт profile и открывает dashboard.
          </p>
        </section>
        <AdminTrainerApplicationsDashboard />
      </main>
    </ProtectedPage>
  );
}
