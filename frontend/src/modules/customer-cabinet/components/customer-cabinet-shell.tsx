import Link from 'next/link';
import { CustomerCabinetNav } from '@/modules/customer-cabinet/components/customer-cabinet-nav';

type CustomerCabinetShellProps = {
  title: string;
  description: string;
  children: React.ReactNode;
  actions?: React.ReactNode;
};

export function CustomerCabinetShell({ title, description, children, actions }: CustomerCabinetShellProps) {
  return (
    <section className="customer-cabinet-shell">
      <div className="customer-cabinet-topbar">
        <div>
          <span className="premium-eyebrow">Личный кабинет</span>
          <h1>{title}</h1>
          <p>{description}</p>
        </div>
        <div className="customer-page-actions">
          {actions}
          <Link href="/catalog" className="premium-secondary-button">Каталог</Link>
        </div>
      </div>

      <div className="customer-cabinet-layout">
        <aside className="customer-cabinet-sidebar">
          <div className="customer-cabinet-sidebar-card">
            <strong>TrainerHub</strong>
            <span>Программы, доступы и покупки в одном пространстве.</span>
          </div>
          <CustomerCabinetNav />
        </aside>
        <div className="customer-cabinet-content">{children}</div>
      </div>
    </section>
  );
}
