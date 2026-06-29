import Link from 'next/link';
import { TrainerDashboardShell } from '@/modules/trainer-dashboard/components/trainer-dashboard-shell';
import { TrainerUploadPanel } from '@/modules/upload/components/trainer-upload-panel';

export default function TrainerVideosPage() {
  return (
    <TrainerDashboardShell
      title="Видео и материалы"
      description="Загрузка видео, сборка программ и подготовка материалов к продаже"
    >
      <section className="trainer-video-studio-workbench">
        <header className="trainer-video-studio-hero">
          <div className="trainer-video-studio-hero-content">
            <span className="trainer-video-studio-eyebrow">СТУДИЯ МАТЕРИАЛОВ</span>
            <h2>Видео и материалы</h2>
            <p>Загружайте видеоуроки, собирайте программы и наборы, затем публикуйте их в каталоге.</p>
          </div>
          <div className="trainer-video-studio-actions">
            <Link className="premium-primary-button" href="/trainer/videos?intent=upload">Загрузить видео</Link>
            <Link className="premium-secondary-button" href="/trainer/dashboard/products">Создать продукт</Link>
            <Link className="premium-secondary-button" href="/trainer/dashboard/analytics">Посмотреть аналитику</Link>
          </div>
        </header>
        <TrainerUploadPanel compactHero />
      </section>
    </TrainerDashboardShell>
  );
}
