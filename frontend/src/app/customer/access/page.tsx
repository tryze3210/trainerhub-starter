'use client';

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import { ProtectedPage } from '@/components/protected-page';
import { privateApi } from '@/lib/api';
import type { AccessCenterItem, AccessCenterPayload } from '@/types/api';

function formatDate(value?: string | null): string {
  if (!value) return '—';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat('ru-RU', { dateStyle: 'medium', timeStyle: 'short' }).format(date);
}

function statusLabel(item: AccessCenterItem): string {
  if (item.is_available) return 'Доступен';
  if (item.status === 'expired') return 'Истёк';
  if (item.status === 'revoked') return 'Отозван';
  return item.status || 'unknown';
}

function statusClass(item: AccessCenterItem): string {
  if (item.is_available) return 'badge success';
  if (item.status === 'expired' || item.status === 'revoked') return 'badge danger';
  return 'badge warning';
}

function typeLabel(value: string): string {
  if (value === 'video') return 'Видео';
  if (value === 'program') return 'Программа';
  if (value === 'bundle') return 'Bundle';
  if (value === 'library') return 'Библиотека';
  return value;
}

export default function CustomerAccessCenterPage() {
  const [payload, setPayload] = useState<AccessCenterPayload | null>(null);
  const [loading, setLoading] = useState(true);
  const [msg, setMsg] = useState('');

  async function load() {
    try {
      setLoading(true);
      setMsg('');
      setPayload(await privateApi.getAccessCenter(30));
    } catch (err) {
      setMsg(err instanceof Error ? err.message : 'Не удалось загрузить access center');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  const activeItems = useMemo(() => (payload?.items || []).filter((item) => item.is_available), [payload]);
  const inactiveItems = useMemo(() => (payload?.items || []).filter((item) => !item.is_available), [payload]);

  return (
    <ProtectedPage title="Access center" description="Коммерческие доступы доступны только после входа.">
      <section className="stack" style={{ gap: 24 }}>
        <div className="row" style={{ alignItems: 'flex-start' }}>
          <div className="stack" style={{ gap: 10 }}>
            <span className="badge warning">Commercial access</span>
            <h1>Access center</h1>
            <p className="lead">Единый экран для купленного контента: entitlement, библиотека, срок действия и ссылка на storefront.</p>
          </div>
          <div className="inline">
            <button className="button secondary" onClick={() => void load()} disabled={loading}>Обновить</button>
            <Link className="button ghost" href="/customer/hub">Customer hub</Link>
          </div>
        </div>

        {msg ? <div className="card error">{msg}</div> : null}
        {loading ? <div className="card"><p className="muted">Загружаем доступы…</p></div> : null}

        {payload ? (
          <>
            <div className="grid-4">
              <div className="card"><div className="kpi"><span className="muted">Всего</span><strong>{payload.summary.total_count}</strong></div></div>
              <div className="card"><div className="kpi"><span className="muted">Активные</span><strong>{payload.summary.active_count}</strong></div></div>
              <div className="card"><div className="kpi"><span className="muted">Истекают</span><strong>{payload.summary.expiring_soon_count || 0}</strong></div></div>
              <div className="card"><div className="kpi"><span className="muted">Library</span><strong>{payload.summary.library_access_active ? 'ON' : 'OFF'}</strong></div></div>
            </div>

            <div className="card">
              <h2 className="title-md">Активная библиотека</h2>
              {activeItems.length ? (
                <div className="stack" style={{ gap: 12, marginTop: 14 }}>
                  {activeItems.map((item) => (
                    <div key={item.id} className="card compact">
                      <div className="row" style={{ alignItems: 'flex-start' }}>
                        <div className="stack" style={{ gap: 6 }}>
                          <div className="inline">
                            <span className={statusClass(item)}>{statusLabel(item)}</span>
                            <span className="badge secondary">{typeLabel(item.target_type)}</span>
                          </div>
                          <strong>{item.title || item.target_type}</strong>
                          <p className="muted">Тренер: {item.trainer_name || '—'} · До: {formatDate(item.ends_at)}</p>
                        </div>
                        <Link href={item.access_url || '/customer/access'} className="button secondary">Открыть</Link>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="empty-state"><h3>Активных доступов пока нет</h3><p>После оплаты контент появится здесь автоматически.</p></div>
              )}
            </div>

            <div className="grid-2">
              <div className="card">
                <h3 className="title-md">Readiness</h3>
                <div className="stack" style={{ gap: 10, marginTop: 12 }}>
                  {(payload.readiness || []).map((item) => (
                    <div key={item.code} className="row">
                      <span className={item.is_ok ? 'badge success' : 'badge warning'}>{item.is_ok ? 'OK' : 'Check'}</span>
                      <span>{item.label}</span>
                    </div>
                  ))}
                </div>
              </div>
              <div className="card">
                <h3 className="title-md">Неактивные доступы</h3>
                <div className="stack" style={{ gap: 8, marginTop: 12 }}>
                  {inactiveItems.slice(0, 8).map((item) => (
                    <div key={item.id} className="row">
                      <span className={statusClass(item)}>{statusLabel(item)}</span>
                      <span>{item.title || item.target_type}</span>
                    </div>
                  ))}
                  {!inactiveItems.length ? <p className="muted">Нет неактивных доступов.</p> : null}
                </div>
              </div>
            </div>
          </>
        ) : null}
      </section>
    </ProtectedPage>
  );
}
