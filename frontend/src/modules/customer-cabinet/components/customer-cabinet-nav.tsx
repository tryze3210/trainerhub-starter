'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

export type CustomerNavItem = {
  href: string;
  label: string;
  description?: string;
};

const navItems: CustomerNavItem[] = [
  { href: '/cabinet', label: 'Обзор', description: 'Главная панель' },
  { href: '/learning', label: 'Моё обучение', description: 'Курсы и уроки' },
  { href: '/entitlements', label: 'Доступы', description: 'Активные права' },
  { href: '/orders', label: 'Заказы', description: 'История покупок' },
  { href: '/payments', label: 'Платежи', description: 'Оплаты и статусы' },
  { href: '/subscriptions', label: 'Подписки', description: 'Продления' },
  { href: '/messages', label: 'Сообщения', description: 'Диалоги' },
  { href: '/cabinet', label: 'Профиль', description: 'Аккаунт' },
];

function isActive(pathname: string | null, href: string, label: string) {
  if (label === 'Профиль') return pathname === '/cabinet';
  return pathname === href || Boolean(pathname?.startsWith(`${href}/`));
}

export function CustomerCabinetNav() {
  const pathname = usePathname();

  return (
    <nav className="customer-cabinet-nav" aria-label="Разделы личного кабинета">
      {navItems.map((item) => (
        <Link
          key={`${item.href}-${item.label}`}
          href={item.href}
          className={isActive(pathname, item.href, item.label) ? 'customer-cabinet-nav-link customer-cabinet-nav-link-active' : 'customer-cabinet-nav-link'}
          aria-current={isActive(pathname, item.href, item.label) ? 'page' : undefined}
        >
          <strong>{item.label}</strong>
          {item.description ? <span>{item.description}</span> : null}
        </Link>
      ))}
    </nav>
  );
}
