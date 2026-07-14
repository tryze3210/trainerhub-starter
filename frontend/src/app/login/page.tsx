'use client';
import { Suspense } from 'react';

import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { useEffect, useState } from 'react';
import { useAuthSession } from '@/components/auth-provider';
import { authApi } from '@/lib/api';
import { persistTokens } from '@/lib/auth';
import { isAdminUser } from '@/lib/authz';

function LoginPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const nextPathFromQuery = searchParams.get('next') || '';
  const { user, isAuthenticated, refreshSession } = useAuthSession();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState('');

  useEffect(() => {
    if (isAuthenticated) {
      router.replace(nextPathFromQuery || (isAdminUser(user) ? '/admin' : user?.active_role === 'trainer' ? '/trainer/dashboard' : '/cabinet'));
    }
  }, [isAuthenticated, nextPathFromQuery, router, user]);

  async function onSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    try {
      setLoading(true);
      setMsg('');
      const payload = await authApi.login({ email, password });
      persistTokens(payload.access_token, payload.refresh_token);
      await refreshSession();
      const nextPath =
        nextPathFromQuery ||
        (isAdminUser(payload.user)
          ? '/admin'
          : payload.user.active_role === 'trainer'
            ? '/trainer/dashboard'
            : '/cabinet');
      router.push(nextPath);
      router.refresh();
    } catch (err) {
      setMsg(err instanceof Error ? err.message : 'Не удалось выполнить вход');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="premium-landing premium-auth-page premium-login-page">
      <div className="premium-container premium-auth-layout">
        <section className="premium-auth-copy" aria-labelledby="login-title">
          <span className="premium-eyebrow">TRAINERHUB ACCESS</span>
          <h1 className="premium-hero-title" id="login-title">
            Войти в TrainerHub
          </h1>
          <p className="premium-hero-subtitle">
            Один вход открывает клиентский кабинет, обучение, покупки и рабочее пространство тренера с продуктами,
            аналитикой и сопровождением учеников.
          </p>
          <div className="premium-auth-proof" aria-label="Что доступно после входа">
            <span>Личный кабинет</span>
            <span>Доступы после оплаты</span>
            <span>Trainer dashboard</span>
            <span>Прогресс и материалы</span>
          </div>
        </section>

        <div className="premium-auth-card">
          <div className="premium-auth-card-header">
            <span className="premium-eyebrow">SECURE LOGIN</span>
            <h2>Доступ к аккаунту</h2>
            <p>Тренер попадает в dashboard shell. Клиент продолжает работу в обычном кабинете.</p>
          </div>

          <form className="premium-auth-form" onSubmit={onSubmit}>
            <label className="premium-auth-field" htmlFor="email">
              <span>Email</span>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoComplete="email"
                required
              />
            </label>

            <label className="premium-auth-field" htmlFor="password">
              <span>Пароль</span>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="current-password"
                required
              />
            </label>

            {msg ? (
              <div className="premium-auth-message premium-auth-message-error">
                {msg}
              </div>
            ) : null}

            <button className="premium-primary-button premium-auth-submit" type="submit" disabled={loading}>
              {loading ? 'Входим...' : 'Войти'}
            </button>
          </form>

          <div className="premium-auth-footer">
            <span>Нет аккаунта?</span>
            <Link href="/register">Создать</Link>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={<div className="premium-auth-fallback">Загрузка...</div>}>
      <LoginPageContent />
    </Suspense>
  );
}
