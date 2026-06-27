'use client';

import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { useAuthSession } from '@/components/auth-provider';

const publicLinks = [
  { href: '/catalog', label: 'Каталог' },
  { href: '/trainers', label: 'Тренеры' },
];

const studentLinks = [
  { href: '/catalog', label: 'Каталог' },
  { href: '/learning', label: 'Моё обучение' },
  { href: '/messages', label: 'Сообщения' },
];

const trainerLinks = [
  { href: '/catalog', label: 'Каталог' },
  { href: '/trainer/dashboard', label: 'Кабинет тренера' },
  { href: '/trainer/dashboard', label: 'Ученики' },
  { href: '/trainer/business', label: 'Продажи' },
];

const adminLinks = [
  { href: '/admin', label: 'Admin' },
  { href: '/admin/operations', label: 'Операции' },
  { href: '/admin/payments', label: 'Финансы' },
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

  const links = !isAuthenticated ? publicLinks : isAdmin ? adminLinks : isTrainer ? trainerLinks : studentLinks;
  const profileHref = isAdmin ? '/admin' : isTrainer ? '/trainer/dashboard' : '/cabinet';
  const profileLabel = isAdmin || isTrainer ? 'Профиль' : 'Кабинет';

  function isActive(href: string) {
    if (href === '/') return pathname === '/';
    return pathname === href || Boolean(pathname?.startsWith(`${href}/`));
  }

  return (
    <>
      <nav className="premium-nav" aria-label="Основная навигация">
        {links.map((link) => (
          <Link
            key={`${link.href}-${link.label}`}
            href={link.href}
            className={isActive(link.href) ? 'premium-nav__link premium-nav__link-active' : 'premium-nav__link'}
            aria-current={isActive(link.href) ? 'page' : undefined}
          >
            {link.label}
          </Link>
        ))}
      </nav>

      <div className="premium-header-actions">
        {isLoading ? (
          <span className="premium-header-user">Проверяем сессию</span>
        ) : isAuthenticated ? (
          <>
            <div className="premium-header-user">
              <strong>{user?.full_name || user?.email}</strong>
              <span>{user?.active_role || 'user'}</span>
            </div>
            <Link href={profileHref} className="premium-header-ghost">
              {profileLabel}
            </Link>
            <button className="premium-header-cta" type="button" onClick={onSignOut}>Выйти</button>
          </>
        ) : (
          <>
            <Link href="/login" className="premium-header-ghost">Войти</Link>
            <Link href="/register" className="premium-header-cta">Стать тренером</Link>
          </>
        )}
      </div>
    </>
  );
}
