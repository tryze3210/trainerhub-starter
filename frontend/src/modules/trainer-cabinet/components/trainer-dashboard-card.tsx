import { TrainerSectionHeader } from './trainer-section-header';

export function TrainerDashboardCard({ title, description, action, children }: { title: string; description?: string; action?: React.ReactNode; children: React.ReactNode }) {
  return (
    <section className="trainer-dashboard-card">
      <TrainerSectionHeader title={title} description={description}>{action}</TrainerSectionHeader>
      {children}
    </section>
  );
}
