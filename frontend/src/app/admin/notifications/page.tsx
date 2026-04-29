'use client';

import { useEffect, useMemo, useState } from 'react';
import { ProtectedPage } from '@/components/protected-page';
import { notificationsApi, type AdminAnnouncement, type AdminNotificationCenter } from '@/modules/notifications/api';

function badge(status?: string) {
  if (!status) return 'badge secondary';
  if (['ok', 'sent', 'published', 'read', 'success'].includes(status)) return 'badge success';
  if (['failed', 'error', 'attention'].includes(status)) return 'badge error';
  if (['pending', 'draft', 'unread'].includes(status)) return 'badge warning';
  return 'badge secondary';
}

const emptyForm = {
  title: '',
  body: '',
  cta_label: '',
  cta_url: '',
  audience_type: 'all_users' as 'all_users' | 'all_trainers' | 'specific_users',
  publish_now: true,
};

export default function AdminNotificationsPage() {
  const [days, setDays] = useState(30);
  const [center, setCenter] = useState<AdminNotificationCenter | null>(null);
  const [announcements, setAnnouncements] = useState<AdminAnnouncement[]>([]);
  const [form, setForm] = useState(emptyForm);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  async function load() {
    try {
      setLoading(true);
      setError('');
      const [centerPayload, announcementPayload] = await Promise.all([
        notificationsApi.getAdminCenter(days),
        notificationsApi.listAnnouncements(),
      ]);
      setCenter(centerPayload);
      setAnnouncements(announcementPayload);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось загрузить notification center');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, [days]);

  async function createAnnouncement() {
    if (!form.title.trim() || !form.body.trim()) {
      setError('Заполни title и body для анонса.');
      return;
    }
    try {
      setSaving(true);
      setError('');
      await notificationsApi.createAnnouncement(form);
      setForm(emptyForm);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось создать анонс');
    } finally {
      setSaving(false);
    }
  }

  async function publishAnnouncement(id: string) {
    try {
      setSaving(true);
      await notificationsApi.publishAnnouncement(id);
      await load();
    } finally {
      setSaving(false);
    }
  }

  const deliveryRate = useMemo(() => {
    if (!center || center.summary.deliveries_total === 0) return '0%';
    return `${Math.round((center.summary.deliveries_sent / center.summary.deliveries_total) * 100)}%`;
  }, [center]);

  return (
    <ProtectedPage title="Admin notifications" description="Операционный центр уведомлений доступен только администраторам.">
      <section className="stack" style={{ gap: 24 }}>
        <div className="row" style={{ justifyContent: 'space-between', gap: 16, alignItems: 'flex-start' }}>
          <div className="stack" style={{ gap: 10 }}>
            <span className="badge">Engagement ops</span>
            <h1>Notifications & announcements</h1>
            <p className="lead">Единый центр системных сообщений, delivery health и админских анонсов.</p>
          </div>
          <div className="row" style={{ gap: 8 }}>
            {[7, 30, 90].map((value) => (
              <button key={value} type="button" className={`button ${days === value ? 'primary' : 'secondary'}`} onClick={() => setDays(value)}>
                {value}d
              </button>
            ))}
          </div>
        </div>

        {loading ? <div className="card"><p className="muted">Загружаем notification center…</p></div> : null}
        {error ? <div className="card error">{error}</div> : null}

        {center ? (
          <>
            <div className="grid-4">
              <div className="card"><div className="kpi"><span className="muted">Notifications</span><strong>{center.summary.notifications_total}</strong></div></div>
              <div className="card"><div className="kpi"><span className="muted">Unread</span><strong>{center.summary.notifications_unread}</strong></div></div>
              <div className="card"><div className="kpi"><span className="muted">Delivery rate</span><strong>{deliveryRate}</strong></div></div>
              <div className="card"><div className="kpi"><span className="muted">Failed</span><strong>{center.summary.deliveries_failed}</strong></div></div>
            </div>

            <div className="grid-2">
              <div className="card dark hero">
                <div className="stack" style={{ gap: 12 }}>
                  <span className={badge(center.health.status)}>{center.health.status}</span>
                  <h2 className="title-lg" style={{ margin: 0 }}>Notification health</h2>
                  <p>Контролирует backlog, failed deliveries и draft-анонсы, чтобы lifecycle-сообщения не терялись.</p>
                </div>
              </div>

              <div className="card">
                <h2 className="title-md">Health checks</h2>
                <div className="stack" style={{ gap: 10, marginTop: 16 }}>
                  {center.health.checks.map((check) => (
                    <div className="list-item" key={check.code}>
                      <span>{check.title}</span>
                      <span className={badge(check.status)}>{check.value}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="grid-2">
              <div className="card">
                <h2 className="title-md">Создать анонс</h2>
                <div className="stack" style={{ gap: 12, marginTop: 16 }}>
                  <input className="input" placeholder="Заголовок" value={form.title} onChange={(event) => setForm((value) => ({ ...value, title: event.target.value }))} />
                  <textarea className="input" placeholder="Текст анонса" rows={5} value={form.body} onChange={(event) => setForm((value) => ({ ...value, body: event.target.value }))} />
                  <div className="grid-2">
                    <input className="input" placeholder="CTA label" value={form.cta_label} onChange={(event) => setForm((value) => ({ ...value, cta_label: event.target.value }))} />
                    <input className="input" placeholder="CTA url" value={form.cta_url} onChange={(event) => setForm((value) => ({ ...value, cta_url: event.target.value }))} />
                  </div>
                  <select className="input" value={form.audience_type} onChange={(event) => setForm((value) => ({ ...value, audience_type: event.target.value as typeof form.audience_type }))}>
                    <option value="all_users">Все пользователи</option>
                    <option value="all_trainers">Все тренеры</option>
                  </select>
                  <label className="row" style={{ gap: 8 }}>
                    <input type="checkbox" checked={form.publish_now} onChange={(event) => setForm((value) => ({ ...value, publish_now: event.target.checked }))} />
                    Опубликовать сразу и разослать in-app уведомления
                  </label>
                  <button className="button primary" type="button" disabled={saving} onClick={createAnnouncement}>Создать анонс</button>
                </div>
              </div>

              <div className="card">
                <h2 className="title-md">Типы уведомлений</h2>
                <div className="stack" style={{ gap: 10, marginTop: 16 }}>
                  {center.types.length === 0 ? <p className="muted">Пока нет уведомлений за период.</p> : null}
                  {center.types.map((item) => (
                    <div className="list-item" key={item.notification_type}>
                      <span>{item.notification_type}</span>
                      <span className="badge secondary">{item.count} · unread {item.unread}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="card">
              <h2 className="title-md">Анонсы</h2>
              <div className="stack" style={{ gap: 12, marginTop: 16 }}>
                {announcements.length === 0 ? <p className="muted">Анонсов пока нет.</p> : null}
                {announcements.slice(0, 20).map((item) => (
                  <div className="list-item" key={item.id} style={{ alignItems: 'flex-start' }}>
                    <div className="stack" style={{ gap: 4 }}>
                      <div className="row" style={{ gap: 8 }}>
                        <span className={badge(item.is_published ? 'published' : 'draft')}>{item.is_published ? 'published' : 'draft'}</span>
                        <span className="badge secondary">{item.audience_type}</span>
                      </div>
                      <strong>{item.title}</strong>
                      <p className="muted" style={{ margin: 0 }}>{item.body}</p>
                      <small>{item.created_at} · sent {item.notifications_count ?? item.created_notifications ?? 0}</small>
                    </div>
                    {!item.is_published ? (
                      <button className="button secondary" type="button" disabled={saving} onClick={() => publishAnnouncement(item.id)}>Publish</button>
                    ) : null}
                  </div>
                ))}
              </div>
            </div>

            <div className="grid-2">
              <div className="card">
                <h2 className="title-md">Failed deliveries</h2>
                <div className="stack" style={{ gap: 10, marginTop: 16 }}>
                  {center.recent_failed_deliveries.length === 0 ? <p className="muted">Ошибок доставки нет.</p> : null}
                  {center.recent_failed_deliveries.slice(0, 10).map((item, index) => (
                    <div className="list-item" key={`${item.id}-${index}`}>
                      <span>{String(item.user_email || item.user_id || 'user')}</span>
                      <span className="badge error">{String(item.error_message || 'failed')}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="card">
                <h2 className="title-md">Recent notifications</h2>
                <div className="stack" style={{ gap: 10, marginTop: 16 }}>
                  {center.recent_notifications.slice(0, 10).map((item) => (
                    <div className="list-item" key={item.id}>
                      <span>{item.title}</span>
                      <span className={badge(item.is_read ? 'read' : 'unread')}>{item.notification_type}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </>
        ) : null}
      </section>
    </ProtectedPage>
  );
}
