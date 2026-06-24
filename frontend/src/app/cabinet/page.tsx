'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { ProtectedPage } from '@/components/protected-page';
import { useAuthSession } from '@/components/auth-provider';
import { authApi } from '@/lib/api';
import type { SessionPayload } from '@/types/api';

export default function CabinetPage() {
  const { user, isAuthenticated, isLoading: sessionLoading } = useAuthSession();
  const [data, setData] = useState<SessionPayload | null>(null);
  const [loading, setLoading] = useState(true);
  const [msg, setMsg] = useState('');

  useEffect(() => {
    if (sessionLoading) return;
    if (!isAuthenticated) {
      setLoading(false);
      setData(null);
      setMsg('');
      return;
    }

    void (async () => {
      try {
        setLoading(true);
        setMsg('');
        setData(await authApi.me());
      } catch (err) {
        setMsg(err instanceof Error ? err.message : 'Не удалось загрузить кабинет');
      } finally {
        setLoading(false);
      }
    })();
  }, [isAuthenticated, sessionLoading]);

  const activeUser = data?.user || user;
  const isTrainer = activeUser?.active_role === 'trainer';

  return (
    <ProtectedPage title="Личный кабинет" description="Личный кабинет доступен только авторизованным пользователям.">
      <section className="stack" style={{ gap: 24 }}>
        <div className="stack" style={{ gap: 10 }}>
          <span className="badge">Кабинет</span>
          <h1>{isTrainer ? 'Личный кабинет тренера' : 'Личный кабинет'}</h1>
          <p className="lead">
            Базовый customer-кабинет сохранён. Для trainer-ролей добавлен отдельный shell и отдельный onboarding flow.
          </p>
        </div>

        {loading ? <div className="card"><p className="muted">Загружаем данные пользователя…</p></div> : null}
        {msg ? <div className="card error">{msg}</div> : null}

        {activeUser ? (
          <div className="grid-3">
            <div className="card dark hero">
              <div className="stack" style={{ gap: 12 }}>
                <span className="badge secondary">Профиль</span>
                <h2 className="title-lg" style={{ margin: 0 }}>{activeUser.full_name || activeUser.email}</h2>
                <p>{activeUser.email}</p>
                <div className="inline">
                  <span className="badge success">Роль: {activeUser.active_role}</span>
                  <span className="badge">Язык: {activeUser.preferred_language || '—'}</span>
                </div>
              </div>
            </div>

            <div className="card">
              <div className="kpi">
                <span className="muted">Город</span>
                <strong>{activeUser.city || '—'}</strong>
              </div>
              <div className="divider" />
              <div className="kpi">
                <span className="muted">Страна</span>
                <strong>{activeUser.country || '—'}</strong>
              </div>
            </div>

            <div className="card">
              <div className="kpi">
                <span className="muted">Доступные роли</span>
                <strong>{(activeUser.available_roles || []).join(', ') || '—'}</strong>
              </div>
              <div className="divider" />
              <div className="kpi">
                <span className="muted">Телефон</span>
                <strong>{activeUser.phone || '—'}</strong>
              </div>
            </div>
          </div>
        ) : null}

        {isTrainer ? (
          <div className="card success">
            <div className="stack" style={{ gap: 12 }}>
              <strong>Для trainer-ролей кабинет вынесен в отдельный контур.</strong>
              <p className="muted">Здесь оставлен общий аккаунт-блок, а управление профилем тренера, onboarding и upload flow перенесены в отдельный trainer dashboard shell.</p>
              <div className="inline">
                <Link href="/trainer/onboarding" className="button">Открыть onboarding</Link>
                <Link href="/trainer/dashboard" className="button secondary">Открыть dashboard</Link>
                <Link href="/trainer/videos" className="button ghost">Открыть upload flow</Link>
              </div>
            </div>
          </div>
        ) : null}

        <div className="grid-4">
          <Link href="/customer/hub" className="card">
            <h3 className="title-md">Customer hub</h3>
            <p>Библиотека, заказы, подписки, избранное и рекомендации.</p>
          </Link>
          <Link href="/customer/access" className="card">
            <h3 className="title-md">Access center</h3>
            <p>Коммерческие доступы, библиотека и entitlement readiness.</p>
          </Link>
          <Link href="/billing" className="card">
            <h3 className="title-md">Billing</h3>
            <p>Покупки, подписки, чеки, статусы платежей и активные доступы.</p>
          </Link>
          <Link href="/orders" className="card">
            <h3 className="title-md">Заказы</h3>
            <p>История checkout и order flow.</p>
          </Link>
          <Link href="/payments" className="card">
            <h3 className="title-md">Платежи</h3>
            <p>Платёжные записи и статусы provider flow.</p>
          </Link>
          <Link href="/subscriptions" className="card">
            <h3 className="title-md">Подписки</h3>
            <p>Подписочные продукты и жизненный цикл.</p>
          </Link>
          <Link href="/entitlements" className="card">
            <h3 className="title-md">Доступы</h3>
            <p>Выданные права доступа к контенту.</p>
          </Link>
        </div>
      </section>
    </ProtectedPage>
  );
}
