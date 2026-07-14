'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import type { ReactNode } from 'react';

type AdminNavGroup = 'overview' | 'moderation' | 'finance' | 'system';

type AdminNavItem = {
  href: string;
  label: string;
  description: string;
  icon: string;
  group: AdminNavGroup;
};

const NAV_ITEMS: AdminNavItem[] = [
  {
    href: '/admin',
    label: 'Главная',
    description: 'Сводка по платформе и срочным задачам',
    icon: 'ГЛ',
    group: 'overview',
  },
  {
    href: '/admin/operations',
    label: 'Операции',
    description: 'Вебхуки, споры, блокировки и фоновые события',
    icon: 'ОП',
    group: 'system',
  },
  {
    href: '/admin/audit',
    label: 'Журнал действий',
    description: 'История операторских изменений',
    icon: 'ЖД',
    group: 'system',
  },
  {
    href: '/admin/reconciliation',
    label: 'Сверка',
    description: 'Расхождения денег, доступов и событий',
    icon: 'СВ',
    group: 'finance',
  },
  {
    href: '/admin/reconciliation/snapshots',
    label: 'Снимки сверки',
    description: 'История сверок и динамика проблем',
    icon: 'СС',
    group: 'finance',
  },
  {
    href: '/admin/moderation',
    label: 'Модерация',
    description: 'Очереди проверки и спорные материалы',
    icon: 'МД',
    group: 'moderation',
  },
  {
    href: '/admin/trainers/applications',
    label: 'Заявки тренеров',
    description: 'Проверка анкет и допуск к кабинету тренера',
    icon: 'ЗТ',
    group: 'moderation',
  },
  {
    href: '/admin/payouts',
    label: 'Выплаты',
    description: 'Балансы, реестр выплат и ручные проверки',
    icon: 'ВП',
    group: 'finance',
  },
  {
    href: '/admin/referrals',
    label: 'Рефералы',
    description: 'Вознаграждения, атрибуция и антифрод',
    icon: 'РФ',
    group: 'finance',
  },
  {
    href: '/admin/analytics',
    label: 'Аналитика',
    description: 'Выручка, заказы, конверсия и KPI',
    icon: 'АН',
    group: 'overview',
  },
  {
    href: '/admin/marketplace',
    label: 'Маркетплейс',
    description: 'Каталог, продукты, программы и наборы',
    icon: 'МК',
    group: 'overview',
  },
  {
    href: '/admin/reviews',
    label: 'Отзывы',
    description: 'Модерация отзывов',
    icon: 'ОТ',
    group: 'moderation',
  },
  {
    href: '/admin/notifications',
    label: 'Уведомления',
    description: 'Системные уведомления',
    icon: 'УВ',
    group: 'system',
  },
  {
    href: '/admin/subscriptions',
    label: 'Подписки',
    description: 'Планы и подписки',
    icon: 'ПД',
    group: 'finance',
  },
  {
    href: '/admin/settings/payments',
    label: 'Настройки оплат',
    description: 'Провайдеры и комиссии',
    icon: 'НО',
    group: 'system',
  },
];

const GROUP_LABELS: Record<AdminNavGroup, string> = {
  overview: 'Обзор',
  moderation: 'Модерация',
  finance: 'Финансы',
  system: 'Система',
};

function isActivePath(pathname: string, href: string) {
  if (href === '/admin') return pathname === '/admin';
  return pathname === href || pathname.startsWith(`${href}/`);
}

function AdminNavLink({ item, active }: { item: AdminNavItem; active: boolean }) {
  return (
    <Link className={`admin-nav__link ${active ? 'is-active' : ''}`} href={item.href}>
      <span className="admin-nav__icon" aria-hidden="true">{item.icon}</span>
      <span className="admin-nav__text">
        <strong>{item.label}</strong>
        <small>{item.description}</small>
      </span>
    </Link>
  );
}

export function AdminShell({ children }: { children: ReactNode }) {
  const pathname = usePathname() || '/admin';
  const activeItem = NAV_ITEMS.find((item) => isActivePath(pathname, item.href));

  return (
    <section className="admin-shell">
      <div className="admin-layout">
        <aside className="admin-sidebar">
          <div className="admin-sidebar__brand">
            <span className="admin-sidebar__mark" aria-hidden="true">TH</span>
            <div>
              <span className="admin-eyebrow">Админ-панель</span>
              <h1>TrainerHub</h1>
            </div>
            <p>Рабочее место администратора: модерация, выплаты, каталог, аналитика и системные настройки.</p>
          </div>

          {activeItem ? (
            <div className="admin-current-section">
              <span className="admin-nav__group-title">Текущий раздел</span>
              <h2>{activeItem.label}</h2>
              <p>{activeItem.description}</p>
            </div>
          ) : null}

          <nav className="admin-nav" aria-label="Навигация администратора">
            {(['overview', 'moderation', 'finance', 'system'] as const).map((group) => {
              const items = NAV_ITEMS.filter((item) => item.group === group);

              return (
                <div className="admin-nav__group" key={group}>
                  <span className="admin-nav__group-title">{GROUP_LABELS[group]}</span>
                  {items.map((item) => (
                    <AdminNavLink key={item.href} item={item} active={isActivePath(pathname, item.href)} />
                  ))}
                </div>
              );
            })}
          </nav>
        </aside>

        <div className="admin-content">
          {children}
        </div>
      </div>
    </section>
  );
}
