'use client';

import Link from 'next/link';
import { useAuthSession } from '@/components/auth-provider';

export function ProtectedPage({
  title,
  description,
  children,
}: {
  title: string;
  description: string;
  children: React.ReactNode;
}) {
  const { isAuthenticated, isLoading } = useAuthSession();

  if (isLoading) {
    return (
      <section className="stack" style={{ gap: 18 }}>
        <span className="badge secondary">Сессия</span>
        <h1>{title}</h1>
        <p className="lead">Проверяем авторизацию и загружаем данные кабинета.</p>
      </section>
    );
  }

  if (!isAuthenticated) {
    return (
      <section className="stack" style={{ gap: 24 }}>
        <div className="stack" style={{ gap: 10 }}>
          <span className="badge warning">Нужен вход</span>
          <h1>{title}</h1>
          <p className="lead">{description}</p>
        </div>

        <div className="card error">
          <div className="stack" style={{ gap: 10 }}>
            <strong>Эта страница доступна только авторизованным пользователям.</strong>
            <p className="muted">Выполни вход или создай аккаунт, чтобы открыть приватные разделы.</p>
            <div className="inline">
              <Link href="/login" className="button">Войти</Link>
              <Link href="/register" className="button secondary">Регистрация</Link>
            </div>
          </div>
        </div>
      </section>
    );
  }

  return <>{children}</>;
}
