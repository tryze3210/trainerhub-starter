'use client';

import { useEffect, useState } from 'react';
import { ProtectedPage } from '@/components/protected-page';
import { reviewsApi, type TrainerReviewQuality } from '@/modules/reviews/api';

function Metric({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="card compact">
      <span className="muted">{label}</span>
      <strong style={{ display: 'block', fontSize: 24, marginTop: 6 }}>{value}</strong>
    </div>
  );
}

function formatDate(value?: string | null) {
  if (!value) return '—';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : new Intl.DateTimeFormat('ru-RU', { dateStyle: 'medium', timeStyle: 'short' }).format(date);
}

export default function TrainerReviewsPage() {
  const [payload, setPayload] = useState<TrainerReviewQuality | null>(null);
  const [replyDrafts, setReplyDrafts] = useState<Record<string, string>>({});
  const [msg, setMsg] = useState('');

  async function load() {
    try {
      setMsg('');
      setPayload(await reviewsApi.getTrainerQuality(30));
    } catch (err) {
      setMsg(err instanceof Error ? err.message : 'Не удалось загрузить отзывы тренера');
    }
  }

  useEffect(() => {
    void load();
  }, []);

  async function saveReply(reviewId: string) {
    try {
      setMsg('');
      await reviewsApi.replyToReview(reviewId, replyDrafts[reviewId] || '');
      setReplyDrafts((current) => ({ ...current, [reviewId]: '' }));
      await load();
    } catch (err) {
      setMsg(err instanceof Error ? err.message : 'Не удалось сохранить ответ тренера');
    }
  }

  return (
    <ProtectedPage title="Trainer reviews" description="Кабинет качества для тренера.">
      <section className="stack" style={{ gap: 24 }}>
        <div className="row" style={{ alignItems: 'flex-start' }}>
          <div className="stack" style={{ gap: 10 }}>
            <span className="badge secondary">Quality</span>
            <h1>Отзывы и качество контента</h1>
            <p className="lead">Сводка по оценкам, проблемным отзывам и контенту, который требует улучшения.</p>
          </div>
          <button className="button secondary" onClick={() => void load()}>Обновить</button>
        </div>

        {msg ? <div className="card error">{msg}</div> : null}

        {payload ? (
          <>
            <div className="grid-4">
              <Metric label="Всего отзывов" value={payload.summary.total_reviews} />
              <Metric label="Published" value={payload.summary.published_count} />
              <Metric label="Pending" value={payload.summary.pending_count} />
              <Metric label="Avg rating" value={payload.summary.average_rating} />
            </div>

            <div className="grid-2">
              <section className="card">
                <h2>Контент по рейтингу</h2>
                <div className="stack" style={{ gap: 12, marginTop: 16 }}>
                  {payload.by_target.length ? payload.by_target.map((item) => (
                    <div className="list-item" key={`${item.target_type}-${item.target_id}`}>
                      <span className="muted">{item.target_type}</span>
                      <strong>{item.target_title}</strong>
                      <span>{item.average_rating}/5 · {item.reviews_count} отзывов</span>
                    </div>
                  )) : <p className="muted">По контенту пока нет опубликованных отзывов.</p>}
                </div>
              </section>

              <section className="card">
                <h2>Readiness</h2>
                <div className="stack" style={{ gap: 12, marginTop: 16 }}>
                  {payload.readiness.map((item) => (
                    <div className="list-item" key={item.code}>
                      <span className={item.is_ok ? 'badge success' : 'badge warning'}>{item.is_ok ? 'ok' : 'attention'}</span>
                      <strong>{item.label}</strong>
                    </div>
                  ))}
                </div>
              </section>
            </div>

            <section className="card">
              <h2>Последние отзывы</h2>
              <div className="stack" style={{ gap: 12, marginTop: 16 }}>
                {payload.recent_reviews.length ? payload.recent_reviews.map((item) => (
                  <article className="card compact" key={item.id}>
                    <div className="row">
                      <strong>{item.title}</strong>
                      <span className="badge secondary">{item.status}</span>
                    </div>
                    <p className="muted">{item.target_title || item.target_id} · {formatDate(item.created_at)}</p>
                    <p>{item.body}</p>
                    {item.trainer_reply ? (
                      <div className="card compact">
                        <span className="badge secondary">Ответ тренера</span>
                        <p style={{ marginTop: 8 }}>{item.trainer_reply}</p>
                      </div>
                    ) : null}
                    <div className="stack" style={{ gap: 8 }}>
                      <textarea
                        className="textarea"
                        rows={3}
                        value={replyDrafts[item.id] ?? item.trainer_reply ?? ''}
                        onChange={(event) => setReplyDrafts((current) => ({ ...current, [item.id]: event.target.value }))}
                        placeholder="Ответить ученику публично"
                      />
                      <button className="button secondary" type="button" onClick={() => void saveReply(item.id)}>
                        Сохранить ответ
                      </button>
                    </div>
                  </article>
                )) : <p className="muted">Отзывов пока нет.</p>}
              </div>
            </section>
          </>
        ) : null}
      </section>
    </ProtectedPage>
  );
}
