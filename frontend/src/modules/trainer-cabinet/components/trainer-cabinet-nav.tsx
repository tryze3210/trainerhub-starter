'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

export type TrainerNavItem = {
  href: string;
  label: string;
  description?: string;
};

const navItems: TrainerNavItem[] = [
  { href: '/trainer/dashboard', label: 'Обзор', description: 'Главная панель' },
  { href: '/trainer/business', label: 'Бизнес', description: 'Финансы и риски' },
  { href: '/trainer/dashboard/products', label: 'Продукты', description: 'Курсы и программы' },
  { href: '/trainer/videos', label: 'Видео', description: 'Материалы' },
  { href: '/trainer/dashboard/crm', label: 'Ученики', description: 'Клиенты и сегменты' },
  { href: '/trainer/dashboard/assignments', label: 'Задания', description: 'Ответы учеников' },
  { href: '/trainer/dashboard/schedule', label: 'Расписание', description: 'Записи и занятия' },
  { href: '/trainer/dashboard/sales', label: 'Продажи', description: 'Покупки и конверсия' },
  { href: '/trainer/dashboard/revenue', label: 'Доход', description: 'Выручка' },
  { href: '/trainer/dashboard/payouts', label: 'Выплаты', description: 'Заявки' },
  { href: '/trainer/dashboard/analytics', label: 'Аналитика', description: 'Метрики контента' },
  { href: '/trainer/reviews', label: 'Отзывы', description: 'Качество' },
  { href: '/trainer/onboarding', label: 'Профиль', description: 'Публичная карточка' },
  { href: '/trainer/application-status', label: 'Статус', description: 'Проверка' },
];

export function TrainerCabinetNav() {
  const pathname = usePathname();
  return (
    <nav className="trainer-cabinet-nav" aria-label="Разделы кабинета тренера">
      {navItems.map((item) => {
        const active = pathname === item.href || Boolean(pathname?.startsWith(`${item.href}/`));
        return (
          <Link key={item.href} href={item.href} className={active ? 'trainer-cabinet-nav-link trainer-cabinet-nav-link-active' : 'trainer-cabinet-nav-link'} aria-current={active ? 'page' : undefined}>
            <strong>{item.label}</strong>
            {item.description ? <span>{item.description}</span> : null}
          </Link>
        );
      })}
    </nav>
  );
}
