'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { ProtectedPage } from '@/components/protected-page';
import { notificationsApi, type NotificationInbox } from '@/modules/notifications/api';

function badge(status?: string) {
  if (!status) return 'badge secondary';
  if (['sent', 'read', 'ok', 'success'].includes(status)) return 'badge success';
  if (['failed', 'error', 'attention'].includes(status)) return 'badge error';
  if (['pending', 'unread'].includes(status)) return 'badge warning';
  return 'badge secondary';
}

export default function NotificationsPage() {
  const [inbox, setInbox] = useState<NotificationInbox | null>(null);
  const [unreadOnly, setUnreadOnly] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  async function load() {
    try {
      setLoading(true);
      setError('');
      setInbox(await notificationsApi.getInbox({ unread: unreadOnly, limit: 80 }));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось загрузить уведомления');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, [unreadOnly]);

  async function markRead(id: string) {
    await notificationsApi.markRead(id);
    await load();
  }

  async function markAllRead() {
    try {
      setSaving(true);
      await notificationsApi.markAllRead();
      await load();
    } finally {
      setSaving(false);
    }
  }

  async function togglePreference(key: 'in_app_enabled' | 'email_enabled' | 'marketing_enabled' | 'product_updates_enabled') {
    if (!inbox) return;
    const nextValue = !inbox.preferences[key];
    await notificationsApi.updatePreferences({ [key]: nextValue });
    await load();
  }

  return (
    <ProtectedPage title="Notifications" description="Центр уведомлений пользователя.">
      <section className="stack" style={{ gap: 24 }}>
        <div className="row" style={{ justifyContent: 'space-between', gap: 16, alignItems: 'flex-start' }}>
          <div className="stack" style={{ gap: 10 }}>
            <span className="badge">Engagement center</span>
            <h1>Notifications</h1>
            <p className="lead">Покупки, подписки, модерация, выплаты и системные сообщения в одном inbox.</p>
          </div>
          <div className="row" style={{ gap: 8 }}>
            <button className={`button ${unreadOnly ? 'primary' : 'secondary'}`} type="button" onClick={() => setUnreadOnly((value) => !value)}>
              Только непрочитанные
            </button>
            <button className="button secondary" type="button" disabled={saving} onClick={markAllRead}>
              Отметить все прочитанными
            </button>
          </div>
        </div>

        {loading ? <div className="card"><p className="muted">Загружаем уведомления…</p></div> : null}
        {error ? <div className="card error">{error}</div> : null}

        {inbox ? (
          <>
            <div className="grid-4">
              <div className="card"><div className="kpi"><span className="muted">Всего</span><strong>{inbox.summary.total}</strong></div></div>
              <div className="card"><div className="kpi"><span className="muted">Непрочитанные</span><strong>{inbox.summary.unread}</strong></div></div>
              <div className="card"><div className="kpi"><span className="muted">Прочитанные</span><strong>{inbox.summary.read}</strong></div></div>
              <div className="card"><div className="kpi"><span className="muted">Типов</span><strong>{Object.keys(inbox.summary.by_type || {}).length}</strong></div></div>
            </div>

            <div className="grid-2">
              <div className="card">
                <h2 className="title-md">Настройки</h2>
                <div className="stack" style={{ gap: 10, marginTop: 16 }}>
                  {([
                    ['in_app_enabled', 'In-app уведомления'],
                    ['email_enabled', 'Email уведомления'],
                    ['marketing_enabled', 'Маркетинговые сообщения'],
                    ['product_updates_enabled', 'Продуктовые обновления'],
                  ] as const).map(([key, label]) => (
                    <button key={key} className="list-item" type="button" onClick={() => togglePreference(key)}>
                      <span>{label}</span>
                      <span className={badge(inbox.preferences[key] ? 'sent' : 'failed')}>{inbox.preferences[key] ? 'on' : 'off'}</span>
                    </button>
                  ))}
                </div>
              </div>

              <div className="card dark hero">
                <div className="stack" style={{ gap: 12 }}>
                  <span className={badge(inbox.summary.unread ? 'pending' : 'ok')}>{inbox.summary.unread ? 'needs attention' : 'clean'}</span>
                  <h2 className="title-lg" style={{ margin: 0 }}>Inbox health</h2>
                  <p>Непрочитанные уведомления используются для customer/trainer lifecycle: доступы, выплаты, модерация и системные анонсы.</p>
                  <Link className="button" href="/customer/hub">Customer hub</Link>
                </div>
              </div>
            </div>

            <div className="card">
              <h2 className="title-md">Последние уведомления</h2>
              <div className="stack" style={{ gap: 12, marginTop: 16 }}>
                {inbox.results.length === 0 ? <p className="muted">Уведомлений пока нет.</p> : null}
                {inbox.results.map((item) => (
                  <div className="list-item" key={item.id} style={{ alignItems: 'flex-start' }}>
                    <div className="stack" style={{ gap: 4 }}>
                      <div className="row" style={{ gap: 8 }}>
                        <span className={badge(item.is_read ? 'read' : 'pending')}>{item.is_read ? 'read' : 'unread'}</span>
                        <span className="badge secondary">{item.notification_type}</span>
                      </div>
                      <strong>{item.title}</strong>
                      <p className="muted" style={{ margin: 0 }}>{item.body}</p>
                      {item.cta_url ? <Link href={item.cta_url}>{item.cta_label || 'Открыть'}</Link> : null}
                    </div>
                    {!item.is_read ? (
                      <button className="button secondary" type="button" onClick={() => markRead(item.id)}>Прочитано</button>
                    ) : null}
                  </div>
                ))}
              </div>
            </div>
          </>
        ) : null}
      </section>
    </ProtectedPage>
  );
}
