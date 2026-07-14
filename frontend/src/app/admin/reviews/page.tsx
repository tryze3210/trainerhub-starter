'use client';

import { useEffect, useState } from 'react';
import { ProtectedPage } from '@/components/protected-page';
import { useAuthSession } from '@/components/auth-provider';
import { isAdminUser } from '@/lib/authz';
import { reviewsApi, type Review, type ReviewTrustCenter } from '@/modules/reviews/api';

function formatDate(value?: string | null) {
  if (!value) return '—';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : new Intl.DateTimeFormat('ru-RU', { dateStyle: 'medium', timeStyle: 'short' }).format(date);
}

function Metric({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="card compact">
      <span className="muted">{label}</span>
      <strong style={{ display: 'block', fontSize: 24, marginTop: 6 }}>{value}</strong>
    </div>
  );
}

export default function AdminОтзывыPage() {
  const { user } = useAuthSession();
  const [items, setItems] = useState<Review[]>([]);
  const [overview, setOverview] = useState<ReviewTrustCenter | null>(null);
  const [statusFilter, setStatusFilter] = useState('pending');
  const [note, setNote] = useState('');
  const [msg, setMsg] = useState('');
  const [busyId, setBusyId] = useState<string | null>(null);
  const isAdmin = isAdminUser(user);

  async function load() {
    try {
      setMsg('');
      const [overviewPayload, reviewsPayload] = await Promise.all([
        reviewsApi.getAdminTrustCenter(30),
        reviewsApi.listAdminReviews(statusFilter),
      ]);
      setOverview(overviewPayload);
      setItems(reviewsPayload);
    } catch (err) {
      setMsg(err instanceof Error ? err.message : 'Не удалось загрузить отзывы');
    }
  }

  useEffect(() => {
    if (!isAdmin) return;
    void load();
  }, [isAdmin, statusFilter]);

  async function moderate(reviewId: string, decision: 'publish' | 'reject' | 'flag') {
    try {
      setBusyId(reviewId);
      setMsg('');
      await reviewsApi.moderateReview(reviewId, decision, note);
      setNote('');
      await load();
    } catch (err) {
      setMsg(err instanceof Error ? err.message : 'Не удалось обновить статус отзыва');
    } finally {
      setBusyId(null);
    }
  }

  return (
    <ProtectedPage title="Модерация отзывов" description="Раздел модерации доступен только администраторам.">
      {!isAdmin ? (
        <div className="card error">У текущей сессии нет роли администратора.</div>
      ) : (
        <section className="stack" style={{ gap: 24 }}>
          <div className="row" style={{ alignItems: 'flex-start' }}>
            <div className="stack" style={{ gap: 10 }}>
              <span className="badge secondary">Доверие и качество</span>
              <h1>Отзывы и качество платформы</h1>
              <p className="lead">Модерация проверенных отзывов, контроль низких оценок и состояния доверия маркетплейса.</p>
            </div>
            <button className="button secondary" onClick={() => void load()}>Обновить</button>
          </div>

          {overview ? (
            <div className="grid-4">
              <Metric label="Ожидают проверки" value={overview.pending_count} />
              <Metric label="Опубликовано" value={overview.published_count} />
              <Metric label="Проверенная покупка" value={overview.verified_purchase_count} />
              <Metric label="Средний рейтинг" value={overview.average_rating} />
            </div>
          ) : null}

          <div className="card">
            <div className="grid-2">
              <div className="form-group">
                <label className="label" htmlFor="review-status">Статус очереди</label>
                <select id="review-status" className="select" value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>
                  <option value="pending">Ожидает проверки</option>
                  <option value="published">Опубликован</option>
                  <option value="rejected">Отклонено</option>
                  <option value="flagged">С флагом</option>
                  <option value="all">Все</option>
                </select>
              </div>
              <div className="form-group">
                <label className="label" htmlFor="moderation-note">Комментарий модератора</label>
                <input id="moderation-note" className="input" value={note} onChange={(event) => setNote(event.target.value)} placeholder="Причина отклонения или флага" />
              </div>
            </div>
          </div>

          {msg ? <div className="card error">{msg}</div> : null}

          {items.length === 0 ? (
            <div className="empty-state"><h3>Очередь пуста</h3><p>Для выбранного статуса отзывов нет.</p></div>
          ) : (
            <div className="grid-2">
              {items.map((item) => (
                <article className="card" key={item.id}>
                  <div className="stack" style={{ gap: 12 }}>
                    <div className="row">
                      <strong>{item.title}</strong>
                      <div className="inline">
                        {item.verified_purchase ? <span className="badge success">проверено</span> : null}
                        <span className="badge warning">{item.status}</span>
                      </div>
                    </div>
                    <p className="muted">{item.target_title || item.target_id} · {item.target_type}</p>
                    <p>{item.body}</p>
                    <div className="grid-2">
                      <div className="list-item"><span className="muted">Автор</span><strong>{item.author_name}</strong></div>
                      <div className="list-item"><span className="muted">Рейтинг</span><strong>{item.rating}/5</strong></div>
                      <div className="list-item"><span className="muted">Создан</span><strong>{formatDate(item.created_at)}</strong></div>
                      <div className="list-item"><span className="muted">Флаги</span><strong>{item.quality_flags?.length ? item.quality_flags.join(', ') : '—'}</strong></div>
                    </div>
                    {item.moderation_note ? <div className="card compact">{item.moderation_note}</div> : null}
                    <div className="inline">
                      <button className="button" disabled={busyId === item.id} onClick={() => void moderate(item.id, 'publish')}>
                        {busyId === item.id ? 'Сохраняем...' : 'Publish'}
                      </button>
                      <button className="button secondary" disabled={busyId === item.id} onClick={() => void moderate(item.id, 'flag')}>
                        Flag
                      </button>
                      <button className="button secondary" disabled={busyId === item.id} onClick={() => void moderate(item.id, 'reject')}>
                        Отклонить
                      </button>
                    </div>
                  </div>
                </article>
              ))}
            </div>
          )}
        </section>
      )}
    </ProtectedPage>
  );
}
