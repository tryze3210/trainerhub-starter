import Link from 'next/link';
import { usePathname } from 'next/navigation';

const links = [
  { href: '/trainer/dashboard', label: 'Dashboard' },
  { href: '/trainer/business', label: 'Business' },
  { href: '/trainer/onboarding', label: 'Onboarding' },
  { href: '/trainer/videos', label: 'Content studio' },
  { href: '/trainers', label: 'Storefront' },
  { href: '/payments', label: 'Платежи' },
  { href: '/orders', label: 'Заказы' },
];

export function TrainerDashboardShell({
  title,
  description,
  children,
}: {
  title: string;
  description: string;
  children: React.ReactNode;
}) {
  const pathname = usePathname();

  return (
    <section className="trainer-dashboard-shell">
      <aside className="trainer-dashboard-shell__sidebar card">
        <div className="stack" style={{ gap: 10 }}>
          <span className="badge">Trainer area</span>
          <h2 className="title-md" style={{ margin: 0 }}>Управление тренером</h2>
          <p className="muted">Trainer-first shell под onboarding, dashboard, content studio и storefront visibility.</p>
        </div>

        <nav className="trainer-side-nav" aria-label="Trainer navigation">
          {links.map((link) => {
            const isActive = pathname === link.href;
            return (
              <Link
                key={link.href}
                href={link.href}
                className={`trainer-side-nav__item${isActive ? ' is-active' : ''}`}
              >
                {link.label}
              </Link>
            );
          })}
        </nav>
      </aside>

      <div className="trainer-dashboard-shell__content stack" style={{ gap: 24 }}>
        <div className="stack" style={{ gap: 10 }}>
          <span className="badge secondary">Trainer dashboard</span>
          <h1>{title}</h1>
          <p className="lead">{description}</p>
        </div>
        {children}
      </div>
    </section>
  );
}
