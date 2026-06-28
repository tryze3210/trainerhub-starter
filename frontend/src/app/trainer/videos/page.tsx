import { TrainerDashboardShell } from '@/modules/trainer-dashboard/components/trainer-dashboard-shell';
import { TrainerUploadPanel } from '@/modules/upload/components/trainer-upload-panel';

export default function TrainerVideosPage() {
  return (
    <TrainerDashboardShell
      title="Видео и материалы"
      description="Загружайте видеоуроки, собирайте программы и наборы, готовьте материалы к публикации в каталоге."
    >
      <TrainerUploadPanel />
    </TrainerDashboardShell>
  );
}
