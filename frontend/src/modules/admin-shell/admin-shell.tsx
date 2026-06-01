'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import type { ReactNode } from 'react';

type AdminNavGroup = 'core' | 'commercial' | 'risk' | 'settings';

type AdminNavItem = {
  href: string;
  label: string;
  description: string;
  group: AdminNavGroup;
};

const NAV_ITEMS: AdminNavItem[] = [
  {
    href: '/admin',
    label: 'Cockpit',
    description: 'Главная сводка marketplace core',
    group: 'core',
  },
  {
    href: '/admin/operations',
    label: 'Operations',
    description: 'Outbox, webhooks, disputes, risk holds',
    group: 'risk',
  },
  {
    href: '/admin/audit',
    label: 'Audit feed',
    description: 'След операторских действий',
    group: 'risk',
  },
  {
    href: '/admin/reconciliation',
    label: 'Reconciliation',
    description: 'Расхождения денег, доступов и событий',
    group: 'risk',
  },
  {
    href: '/admin/reconciliation/snapshots',
    label: 'Snapshots',
    description: 'История reconciliation и тренды',
    group: 'risk',
  },
  {
    href: '/admin/moderation',
    label: 'Moderation',
    description: 'Очереди модерации и risk cases',
    group: 'risk',
  },
  {
    href: '/admin/payouts',
    label: 'Payouts',
    description: 'Выплаты, балансы, ledger',
    group: 'commercial',
  },
  {
    href: '/admin/referrals',
    label: 'Referrals',
    description: 'Ambassador rewards, attribution, integrity',
    group: 'commercial',
  },
  {
    href: '/admin/analytics',
    label: 'Analytics',
    description: 'KPI, revenue, conversion',
    group: 'commercial',
  },
  {
    href: '/admin/marketplace',
    label: 'Marketplace',
    description: 'Командный центр каталога',
    group: 'commercial',
  },
  {
    href: '/admin/reviews',
    label: 'Reviews',
    description: 'Модерация отзывов',
    group: 'risk',
  },
  {
    href: '/admin/notifications',
    label: 'Notifications',
    description: 'Системные уведомления',
    group: 'core',
  },
  {
    href: '/admin/subscriptions',
    label: 'Subscriptions',
    description: 'Планы и подписки',
    group: 'commercial',
  },
  {
    href: '/admin/settings/payments',
    label: 'Payment settings',
    description: 'Провайдеры и комиссии',
    group: 'settings',
  },
];

const GROUP_LABELS: Record<AdminNavGroup, string> = {
  core: 'Core',
  commercial: 'Commercial',
  risk: 'Risk & ops',
  settings: 'Settings',
};

function isActivePath(pathname: string, href: string) {
  if (href === '/admin') return pathname === '/admin';
  return pathname === href || pathname.startsWith(`${href}/`);
}

function AdminNavLink({ item, active }: { item: AdminNavItem; active: boolean }) {
  return (
    <Link className={`trainer-side-nav__item ${active ? 'is-active' : ''}`} href={item.href}>
      <strong>{item.label}</strong>
      <small style={{ display: 'block', marginTop: 4 }}>{item.description}</small>
    </Link>
  );
}

export function AdminShell({ children }: { children: ReactNode }) {
  const pathname = usePathname() || '/admin';
  const activeItem = NAV_ITEMS.find((item) => isActivePath(pathname, item.href));

  return (
    <section className="page">
      <div className="container trainer-dashboard-shell">
        <aside className="trainer-dashboard-shell__sidebar card">
          <span className="badge secondary">Admin console</span>
          <h1 className="title-md" style={{ marginTop: 12 }}>TrainerHub admin</h1>
          <p className="muted">Единая навигация для операций, риска, выплат, referral growth, модерации и аналитики.</p>

          {activeItem ? (
            <div className="list-item" style={{ marginTop: 16 }}>
              <span className="muted">Current section</span>
              <strong>{activeItem.label}</strong>
              <small>{activeItem.description}</small>
            </div>
          ) : null}

          <nav className="trainer-side-nav" aria-label="Admin navigation">
            {(['risk', 'commercial', 'core', 'settings'] as const).map((group) => {
              const items = NAV_ITEMS.filter((item) => item.group === group);

              return (
                <div className="stack" key={group} style={{ gap: 8 }}>
                  <span className="muted" style={{ fontWeight: 700 }}>{GROUP_LABELS[group]}</span>
                  {items.map((item) => (
                    <AdminNavLink key={item.href} item={item} active={isActivePath(pathname, item.href)} />
                  ))}
                </div>
              );
            })}
          </nav>
        </aside>

        <div className="trainer-dashboard-shell__content stack" style={{ gap: 24 }}>
          {children}
        </div>
      </div>
    </section>
  );
}
