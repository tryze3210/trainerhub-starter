'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import type { ReactNode } from 'react';

type AdminNavItem = {
  href: string;
  label: string;
  description: string;
  group: 'core' | 'commercial' | 'risk' | 'settings';
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

const GROUP_LABELS: Record<AdminNavItem['group'], string> = {
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
    <Link
      href={item.href}
      aria-current={active ? 'page' : undefined}
      className={active ? 'card dark' : 'card'}
      style={{
        display: 'block',
        padding: 14,
        textDecoration: 'none',
        borderColor: active ? 'rgba(255,255,255,0.24)' : undefined,
      }}
    >
      <div className="stack" style={{ gap: 4 }}>
        <strong>{item.label}</strong>
        <span className={active ? 'muted-light' : 'muted'} style={{ fontSize: 13, lineHeight: 1.35 }}>
          {item.description}
        </span>
      </div>
    </Link>
  );
}

export function AdminShell({ children }: { children: ReactNode }) {
  const pathname = usePathname() || '/admin';
  const activeItem = NAV_ITEMS.find((item) => isActivePath(pathname, item.href));

  return (
    <div className="stack" style={{ gap: 24 }}>
      <section className="card dark">
        <div className="stack" style={{ gap: 14 }}>
          <div className="inline" style={{ justifyContent: 'space-between', alignItems: 'flex-start', gap: 16 }}>
            <div className="stack" style={{ gap: 8 }}>
              <span className="badge secondary">Admin console</span>
              <div>
                <h1 className="title-lg">TrainerHub admin</h1>
                <p className="lead" style={{ marginTop: 8 }}>
                  Единая навигация для операций, риска, выплат, модерации и аналитики.
                </p>
              </div>
            </div>

            {activeItem ? (
              <div className="card" style={{ minWidth: 220, padding: 14 }}>
                <div className="stack" style={{ gap: 4 }}>
                  <span className="muted">Current section</span>
                  <strong>{activeItem.label}</strong>
                  <span className="muted" style={{ fontSize: 13 }}>{activeItem.description}</span>
                </div>
              </div>
            ) : null}
          </div>

          <div className="inline" style={{ flexWrap: 'wrap', gap: 10 }}>
            <Link href="/admin/operations" className="button">Operations</Link>
            <Link href="/admin/audit" className="button secondary">Audit</Link>
            <Link href="/admin/reconciliation" className="button secondary">Reconciliation</Link>
            <Link href="/admin/reconciliation/snapshots" className="button secondary">Snapshots</Link>
            <Link href="/admin/payouts" className="button secondary">Payouts</Link>
            <Link href="/admin/moderation" className="button secondary">Moderation</Link>
            <Link href="/admin/analytics" className="button ghost">Analytics</Link>
          </div>
        </div>
      </section>

      <section
        style={{
          display: 'grid',
          gridTemplateColumns: 'minmax(220px, 280px) minmax(0, 1fr)',
          gap: 24,
          alignItems: 'start',
        }}
      >
        <aside className="stack" style={{ gap: 14, position: 'sticky', top: 24 }}>
          {(['risk', 'commercial', 'core', 'settings'] as const).map((group) => {
            const items = NAV_ITEMS.filter((item) => item.group === group);
            return (
              <div className="stack" key={group} style={{ gap: 8 }}>
                <span className="badge secondary">{GROUP_LABELS[group]}</span>
                <nav className="stack" style={{ gap: 8 }} aria-label={`${GROUP_LABELS[group]} admin navigation`}>
                  {items.map((item) => (
                    <AdminNavLink key={item.href} item={item} active={isActivePath(pathname, item.href)} />
                  ))}
                </nav>
              </div>
            );
          })}
        </aside>

        <div className="stack" style={{ gap: 24, minWidth: 0 }}>
          {children}
        </div>
      </section>
    </div>
  );
}
