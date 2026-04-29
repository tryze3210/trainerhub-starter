'use client';

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import { ProtectedPage } from '@/components/protected-page';
import { useAuthSession } from '@/components/auth-provider';
import { privateApi } from '@/lib/api';

type EntitlementItem = {
  id: string;
  status?: string;
  access_status?: string;
  access_kind?: string;
  entitlement_type?: string;
  content_type?: string;
  content_title?: string;
  title?: string;
  product_title?: string;
  trainer_name?: string;
  starts_at?: string | null;
  granted_at?: string | null;
  expires_at?: string | null;
  revoked_at?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
  is_active?: boolean;
};

function formatDate(value?: string | null): string {
  if (!value) return '—';

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;

  return new Intl.DateTimeFormat('ru-RU', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(date);
}

function getStatusValue(item: EntitlementItem): string {
  return item.status || item.access_status || (item.is_active ? 'active' : '');
}

function getStatusLabel(item: EntitlementItem): string {
  const status = getStatusValue(item);
  if (!status) return 'unknown';

  const normalized = status.toLowerCase();

  if (normalized === 'active') return 'Активен';
  if (normalized === 'granted') return 'Выдан';
  if (normalized === 'pending') return 'В ожидании';
  if (normalized === 'expired') return 'Истёк';
  if (normalized === 'revoked') return 'Отозван';
  if (normalized === 'inactive') return 'Неактивен';

  return status;
}

function getStatusClass(item: EntitlementItem): string {
  const status = getStatusValue(item);
  if (!status) return 'badge secondary';

  const normalized = status.toLowerCase();

  if (
    normalized === 'active' ||
    normalized === 'granted'
  ) {
    return 'badge success';
  }

  if (normalized === 'pending') {
    return 'badge warning';
  }

  if (
    normalized === 'expired' ||
    normalized === 'revoked' ||
    normalized === 'inactive'
  ) {
    return 'badge danger';
  }

  return 'badge secondary';
}

function getAccessKindLabel(item: EntitlementItem): string {
  const value = item.access_kind || item.entitlement_type || item.content_type;
  if (!value) return '—';

  const normalized = value.toLowerCase();

  if (normalized === 'video') return 'Видео';
  if (normalized === 'program') return 'Программа';
  if (normalized === 'bundle') return 'Bundle';
  if (normalized === 'subscription') return 'Подписка';
  if (normalized === 'one_time') return 'Разовый доступ';

  return value;
}

function getTitle(item: EntitlementItem): string {
  return (
    item.content_title ||
    item.title ||
    item.product_title ||
    'Доступ без названия'
  );
}

function getStartDate(item: EntitlementItem): string {
  return item.starts_at || item.granted_at || item.created_at || '';
}

export default function EntitlementsPage() {
  const [list, setList] = useState<EntitlementItem[]>([]);
  const [msg, setMsg] = useState('');
  const [loading, setLoading] = useState(true);
  const { isAuthenticated, isLoading: sessionLoading } = useAuthSession();

  async function loadEntitlements() {
    try {
      setLoading(true);
      setMsg('');
      const data = await privateApi.listEntitlements();
      setList(Array.isArray(data) ? data : []);
    } catch (err) {
      setMsg(err instanceof Error ? err.message : 'Не удалось загрузить доступы');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (sessionLoading) return;
    if (!isAuthenticated) {
      setLoading(false);
      setMsg('');
      setList([]);
      return;
    }

    void loadEntitlements();
  }, [isAuthenticated, sessionLoading]);

  const stats = useMemo(() => {
    const total = list.length;

    const active = list.filter((item) => {
      const status = getStatusValue(item).toLowerCase();
      return status === 'active' || status === 'granted' || item.is_active;
    }).length;

    const expiring = list.filter((item) => {
      if (!item.expires_at) return false;
      const expires = new Date(item.expires_at);
      const now = new Date();
      const diff = expires.getTime() - now.getTime();
      return diff > 0 && diff <= 1000 * 60 * 60 * 24 * 7;
    }).length;

    const expired = list.filter((item) => {
      const status = getStatusValue(item).toLowerCase();
      return status === 'expired' || status === 'revoked' || status === 'inactive';
    }).length;

    return {
      total,
      active,
      expiring,
      expired,
    };
  }, [list]);

  return (
    <ProtectedPage title="Доступы" description="Права доступа к купленному контенту доступны только после входа.">
      <section className="stack" style={{ gap: 28 }}>
      <div className="row" style={{ alignItems: 'flex-start' }}>
        <div className="stack" style={{ gap: 10 }}>
          <span className="badge warning">Entitlements</span>
          <h1>Доступы</h1>
          <p className="lead">
            Выданные пользователю доступы к контенту. Экран показывает, какие
            права уже активны, какие истекают и какие были отозваны.
          </p>
        </div>

        <div className="inline">
          <button
            className="button secondary"
            onClick={() => void loadEntitlements()}
          >
            Обновить
          </button>
          <Link href="/cabinet" className="button ghost">
            Кабинет
          </Link>
        </div>
      </div>

      <div className="grid-4">
        <div className="card">
          <div className="kpi">
            <span className="muted">Всего доступов</span>
            <strong>{stats.total}</strong>
          </div>
        </div>

        <div className="card">
          <div className="kpi">
            <span className="muted">Активные</span>
            <strong>{stats.active}</strong>
          </div>
        </div>

        <div className="card">
          <div className="kpi">
            <span className="muted">Истекают за 7 дней</span>
            <strong>{stats.expiring}</strong>
          </div>
        </div>

        <div className="card">
          <div className="kpi">
            <span className="muted">Неактивные</span>
            <strong>{stats.expired}</strong>
          </div>
        </div>
      </div>

      {msg ? (
        <div className="card error">
          <div className="stack" style={{ gap: 10 }}>
            <strong>Ошибка загрузки доступов</strong>
            <p className="muted">{msg}</p>
          </div>
        </div>
      ) : loading ? (
        <div className="grid-2">
          {Array.from({ length: 4 }).map((_, idx) => (
            <div className="card" key={idx}>
              <div className="stack" style={{ gap: 12 }}>
                <span className="badge">Загрузка</span>
                <div className="divider" />
                <p className="muted">Получаем список доступов...</p>
              </div>
            </div>
          ))}
        </div>
      ) : list.length === 0 ? (
        <div className="empty-state">
          <h3>Доступов пока нет</h3>
          <p>
            После успешной покупки или активации подписки записи доступа
            появятся в этом разделе.
          </p>
          <div className="inline" style={{ marginTop: 14 }}>
            <Link href="/catalog" className="button">
              Перейти в каталог
            </Link>
            <Link href="/subscriptions" className="button secondary">
              Открыть подписки
            </Link>
          </div>
        </div>
      ) : (
        <>
          <div className="table-wrap">
            <table className="table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Контент</th>
                  <th>Тип</th>
                  <th>Статус</th>
                  <th>Истекает</th>
                </tr>
              </thead>
              <tbody>
                {list.map((item) => (
                  <tr key={item.id}>
                    <td>{item.id}</td>
                    <td>{getTitle(item)}</td>
                    <td>{getAccessKindLabel(item)}</td>
                    <td>
                      <span className={getStatusClass(item)}>
                        {getStatusLabel(item)}
                      </span>
                    </td>
                    <td>{formatDate(item.expires_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="grid-2">
            {list.map((item) => (
              <article className="card" key={`card-${item.id}`}>
                <div className="stack" style={{ gap: 14 }}>
                  <div className="row">
                    <strong>{getTitle(item)}</strong>
                    <span className={getStatusClass(item)}>
                      {getStatusLabel(item)}
                    </span>
                  </div>

                  <div className="grid-2">
                    <div className="list-item">
                      <span className="muted">Entitlement ID</span>
                      <strong>{item.id}</strong>
                    </div>

                    <div className="list-item">
                      <span className="muted">Тип доступа</span>
                      <strong>{getAccessKindLabel(item)}</strong>
                    </div>

                    <div className="list-item">
                      <span className="muted">Тренер</span>
                      <strong>{item.trainer_name || '—'}</strong>
                    </div>

                    <div className="list-item">
                      <span className="muted">Статус</span>
                      <strong>{getStatusLabel(item)}</strong>
                    </div>

                    <div className="list-item">
                      <span className="muted">Выдан / старт</span>
                      <strong>{formatDate(getStartDate(item))}</strong>
                    </div>

                    <div className="list-item">
                      <span className="muted">Истекает</span>
                      <strong>{formatDate(item.expires_at)}</strong>
                    </div>

                    <div className="list-item">
                      <span className="muted">Создан</span>
                      <strong>{formatDate(item.created_at)}</strong>
                    </div>

                    <div className="list-item">
                      <span className="muted">Обновлён</span>
                      <strong>{formatDate(item.updated_at)}</strong>
                    </div>
                  </div>

                  {item.revoked_at ? (
                    <div className="list-item">
                      <span className="muted">Отозван</span>
                      <strong>{formatDate(item.revoked_at)}</strong>
                    </div>
                  ) : null}
                </div>
              </article>
            ))}
          </div>
        </>
      )}
    </section>
    </ProtectedPage>
  );
}