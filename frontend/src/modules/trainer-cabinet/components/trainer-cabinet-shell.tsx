import Link from 'next/link';
import { TrainerCabinetNav } from './trainer-cabinet-nav';
import { TrainerPageHero } from './trainer-page-hero';

export function TrainerCabinetShell({
  title,
  description,
  children,
  actions,
}: {
  title: string;
  description: string;
  children: React.ReactNode;
  actions?: React.ReactNode;
}) {
  return (
    <section className="trainer-cabinet-shell">
      <div className="trainer-cabinet-topbar">
        <TrainerPageHero title={title} description={description} actions={actions} />
      </div>
      <div className="trainer-cabinet-layout">
        <aside className="trainer-cabinet-sidebar">
          <div className="trainer-cabinet-sidebar-card">
            <strong>Кабинет тренера</strong>
            <span>Продукты, ученики, продажи, расписание и выплаты собраны в одном рабочем пространстве.</span>
            <Link href="/catalog" className="premium-secondary-button">Открыть каталог</Link>
          </div>
          <TrainerCabinetNav />
        </aside>
        <div className="trainer-cabinet-content">{children}</div>
      </div>
    </section>
  );
}
