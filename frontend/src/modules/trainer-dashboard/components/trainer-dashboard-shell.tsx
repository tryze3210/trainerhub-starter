'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import type { ReactNode } from 'react';

const links = [
  { href: '/trainer/dashboard', label: 'Dashboard' },
  { href: '/trainer/onboarding', label: 'Onboarding' },
  { href: '/trainer/application-status', label: 'Application status' },
  { href: '/trainer/dashboard/products', label: 'Products' },
  { href: '/trainer/dashboard/sales', label: 'Sales' },
  { href: '/trainer/dashboard/crm', label: 'CRM' },
  { href: '/trainer/dashboard/schedule', label: 'Schedule' },
  { href: '/trainer/dashboard/revenue', label: 'Revenue' },
  { href: '/trainer/dashboard/payouts', label: 'Payouts' },
  { href: '/trainer/dashboard/analytics', label: 'Analytics' },
  { href: '/trainer/business', label: 'Business' },
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
  children: ReactNode;
}) {
  const pathname = usePathname();

  return (
    <section className="trainer-dashboard-shell">
      <aside className="trainer-dashboard-shell__sidebar card">
        <div className="stack" style={{ gap: 10 }}>
          <span className="badge">Trainer area</span>
          <h2 className="title-md" style={{ margin: 0 }}>
            Управление тренером
          </h2>
          <p className="muted">
            Production trainer flow: application review, dashboard unlock, products, revenue and payout operations.
          </p>
        </div>

        <nav className="trainer-side-nav" aria-label="Trainer navigation">
          {links.map((link) => {
            const isActive = pathname === link.href || pathname.startsWith(`${link.href}/`);
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
