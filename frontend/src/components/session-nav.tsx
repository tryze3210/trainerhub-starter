'use client';

import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { useAuthSession } from '@/components/auth-provider';

const publicLinks = [
  { href: '/', label: 'Главная' },
  { href: '/catalog', label: 'Каталог' },
  { href: '/trainers', label: 'Тренеры' },
];

const privateLinks = [
  { href: '/learning', label: 'Обучение' },
  { href: '/assignments', label: 'Задания' },
  { href: '/messages', label: 'Сообщения' },
  { href: '/billing', label: 'Billing' },
  { href: '/subscriptions', label: 'Подписки' },
  { href: '/orders', label: 'Заказы' },
  { href: '/payments', label: 'Платежи' },
  { href: '/entitlements', label: 'Доступы' },
];

export function SessionNav() {
  const pathname = usePathname();
  const router = useRouter();
  const { user, isAuthenticated, isLoading, signOut } = useAuthSession();
  const isTrainer = user?.active_role === 'trainer';
  const isAdmin = user?.active_role === 'admin';

  async function onSignOut() {
    await signOut();
    router.push('/login');
    router.refresh();
  }

  return (
    <>
      <nav className="nav" aria-label="Main navigation">
        {publicLinks.map((link) => (
          <Link key={link.href} href={link.href} aria-current={pathname === link.href ? 'page' : undefined}>
            {link.label}
          </Link>
        ))}
        {isAuthenticated
          ? privateLinks.map((link) => (
              <Link key={link.href} href={link.href} aria-current={pathname === link.href ? 'page' : undefined}>
                {link.label}
              </Link>
            ))
          : null}
        {isAuthenticated && isTrainer ? (
          <>
            <Link href="/trainer/dashboard" aria-current={pathname?.startsWith('/trainer') ? 'page' : undefined}>
              Trainer dashboard
            </Link>
            <Link href="/payouts" aria-current={pathname?.startsWith('/payouts') ? 'page' : undefined}>
              Payouts
            </Link>
          </>
        ) : null}
        {isAuthenticated && isAdmin ? (
          <>
            <Link href="/admin" aria-current={pathname === '/admin' ? 'page' : undefined}>
              Admin cockpit
            </Link>
            <Link href="/admin/moderation" aria-current={pathname?.startsWith('/admin/moderation') ? 'page' : undefined}>
              Moderation
            </Link>
            <Link href="/admin/payouts" aria-current={pathname?.startsWith('/admin/payouts') ? 'page' : undefined}>
              Payout ops
            </Link>
            <Link href="/admin/payments" aria-current={pathname?.startsWith('/admin/payments') ? 'page' : undefined}>
              Payment ops
            </Link>
            <Link href="/admin/analytics" aria-current={pathname?.startsWith('/admin/analytics') ? 'page' : undefined}>
              Analytics
            </Link>
            <Link href="/admin/settings/payments" aria-current={pathname?.startsWith('/admin/settings/payments') ? 'page' : undefined}>
              Payment settings
            </Link>
          </>
        ) : null}
      </nav>

      <div className="inline">
        {isLoading ? (
          <span className="badge secondary">Сессия...</span>
        ) : isAuthenticated ? (
          <>
            <div className="stack" style={{ gap: 2, alignItems: 'flex-end' }}>
              <strong style={{ fontSize: 14 }}>{user?.full_name || user?.email}</strong>
              <span className="muted" style={{ fontSize: 12 }}>{user?.active_role || 'user'}</span>
            </div>
            <Link href={isTrainer ? '/trainer/dashboard' : '/cabinet'} className="button ghost sm">
              {isTrainer ? 'Dashboard' : 'Кабинет'}
            </Link>
            <button className="button secondary sm" type="button" onClick={onSignOut}>Выйти</button>
          </>
        ) : (
          <>
            <Link href="/login" className="button secondary sm">Войти</Link>
            <Link href="/register" className="button sm">Регистрация</Link>
          </>
        )}
      </div>
    </>
  );
}
