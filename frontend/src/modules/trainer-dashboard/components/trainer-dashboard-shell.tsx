'use client';

import { usePathname } from 'next/navigation';
import type { ReactNode } from 'react';
import { DSLayoutNav, DSPageHeader, DSTrainerLayout } from '@/design-system';

const links = [
  { href: '/trainer/dashboard', label: 'Dashboard', description: 'Сводка тренера' },
  { href: '/trainer/onboarding', label: 'Onboarding', description: 'Профиль и approval' },
  { href: '/trainer/application-status', label: 'Application status', description: 'Статус доступа' },
  { href: '/trainer/dashboard/products', label: 'Products', description: 'Курсы и программы' },
  { href: '/trainer/dashboard/assignments', label: 'Homework', description: 'Домашние задания' },
  { href: '/trainer/dashboard/sales', label: 'Sales', description: 'Продажи и конверсия' },
  { href: '/trainer/dashboard/crm', label: 'CRM', description: 'Клиенты и сегменты' },
  { href: '/trainer/dashboard/schedule', label: 'Schedule', description: 'Расписание' },
  { href: '/trainer/dashboard/revenue', label: 'Revenue', description: 'Доход и баланс' },
  { href: '/trainer/dashboard/payouts', label: 'Payouts', description: 'Заявки выплат' },
  { href: '/trainer/dashboard/analytics', label: 'Analytics', description: 'Контент-метрики' },
  { href: '/trainer/business', label: 'Business', description: 'Бизнес cockpit' },
  { href: '/trainer/videos', label: 'Content studio', description: 'Загрузка видео' },
  { href: '/trainers', label: 'Storefront', description: 'Публичный каталог' },
  { href: '/payments', label: 'Платежи', description: 'История оплат' },
  { href: '/orders', label: 'Заказы', description: 'Покупки и заказы' },
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
  const navItems = links.map((link) => ({
    ...link,
    active: pathname === link.href || pathname.startsWith(`${link.href}/`),
  }));

  return (
    <DSTrainerLayout
      sidebar={
        <div className="stack" style={{ gap: 10 }}>
          <span className="badge">Trainer area</span>
          <h2 className="title-md" style={{ margin: 0 }}>
            Управление тренером
          </h2>
          <p className="muted">
            Production trainer flow: application review, dashboard unlock, products, revenue and payout operations.
          </p>
          <DSLayoutNav items={navItems} label="Trainer navigation" />
        </div>
      }
      header={<DSPageHeader eyebrow="Trainer dashboard" title={title} description={description} />}
    >
      <div className="stack" style={{ gap: 24 }}>
        {children}
      </div>
    </DSTrainerLayout>
  );
}
