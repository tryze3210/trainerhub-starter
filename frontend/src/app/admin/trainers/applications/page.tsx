import { ProtectedPage } from '@/components/protected-page';
import { AdminTrainerApplicationsDashboard } from '@/modules/admin-trainer-applications/components/admin-trainer-applications-dashboard';

export default function AdminTrainerApplicationsPage() {
  return (
    <ProtectedPage
      title="Заявки тренеров"
      description="Очередь проверки: одобрение, отклонение, запрос правок и синхронизация доступа тренера."
    >
      <main className="stack page-shell">
        <section className="hero card stack">
          <span className="eyebrow">Проверка тренеров</span>
          <h1>Заявки тренеров</h1>
          <p className="lead">
            Управляй заявками тренеров: одобрение сразу выдаёт роль тренера, создаёт профиль и открывает кабинет.
          </p>
        </section>
        <AdminTrainerApplicationsDashboard />
      </main>
    </ProtectedPage>
  );
}
