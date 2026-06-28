'use client';

import { useEffect, useState } from 'react';
import { ProtectedPage } from '@/components/protected-page';
import { TrainerDashboardShell } from '@/modules/trainer-dashboard/components/trainer-dashboard-shell';
import { TrainerMetricCard, TrainerStatusBadge } from '@/modules/trainer-cabinet/components';
import { trainerStatusLabel, trainerStatusTone, trainerProductTypeLabel } from '@/modules/trainer-cabinet/components/trainer-format';
import { reviewsApi, type TrainerReviewQuality } from '@/modules/reviews/api';

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
    <ProtectedPage title="Отзывы и качество" description="Кабинет качества для тренера.">
      <TrainerDashboardShell
        title="Отзывы и качество"
        description="Следите за оценками продуктов, отвечайте ученикам и находите материалы, которые требуют улучшения."
      >
        <div className="trainer-page-actions">
          <button className="premium-secondary-button" onClick={() => void load()}>Обновить</button>
        </div>

        {msg ? <div className="card error">{msg}</div> : null}

        {payload ? (
          <>
            <div className="trainer-metric-grid">
              <TrainerMetricCard metric={{ label: 'Средний рейтинг', value: payload.summary.average_rating, tone: 'success' }} />
              <TrainerMetricCard metric={{ label: 'Отзывы', value: payload.summary.total_reviews, tone: 'primary' }} />
              <TrainerMetricCard metric={{ label: 'Требуют ответа', value: payload.summary.pending_count, tone: payload.summary.pending_count ? 'warning' : 'neutral' }} />
              <TrainerMetricCard metric={{ label: 'Опубликованы', value: payload.summary.published_count, tone: 'success' }} />
            </div>

            <div className="trainer-review-grid">
              <section className="trainer-section-card">
                <h2>Контент по рейтингу</h2>
                <div className="stack" style={{ gap: 12, marginTop: 16 }}>
                  {payload.by_target.length ? payload.by_target.map((item) => (
                    <div className="list-item" key={`${item.target_type}-${item.target_id}`}>
                      <span className="muted">{trainerProductTypeLabel(item.target_type)}</span>
                      <strong>{item.target_title}</strong>
                      <span>{item.average_rating}/5 · {item.reviews_count} отзывов</span>
                    </div>
                  )) : <p className="muted">По контенту пока нет опубликованных отзывов.</p>}
                </div>
              </section>

              <section className="trainer-section-card">
                <h2>Показатели качества</h2>
                <div className="stack" style={{ gap: 12, marginTop: 16 }}>
                  {payload.readiness.map((item) => (
                    <div className="list-item" key={item.code}>
                      <TrainerStatusBadge tone={item.is_ok ? 'success' : 'warning'}>{item.is_ok ? 'Готово' : 'Требует внимания'}</TrainerStatusBadge>
                      <strong>{item.label}</strong>
                    </div>
                  ))}
                </div>
              </section>
            </div>

            <section className="trainer-section-card">
              <h2>Последние отзывы</h2>
              <div className="trainer-review-grid" style={{ marginTop: 16 }}>
                {payload.recent_reviews.length ? payload.recent_reviews.map((item) => (
                  <article className="trainer-review-card" key={item.id}>
                    <div className="row">
                      <strong>{item.title}</strong>
                      <TrainerStatusBadge tone={trainerStatusTone(item.status)}>{trainerStatusLabel(item.status)}</TrainerStatusBadge>
                    </div>
                    <p className="muted">{item.target_title || item.target_id} · {formatDate(item.created_at)}</p>
                    <p>{item.body}</p>
                    {item.trainer_reply ? (
                      <div className="trainer-review-reply">
                        <TrainerStatusBadge>Ответ тренера</TrainerStatusBadge>
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
                      <button className="premium-secondary-button" type="button" onClick={() => void saveReply(item.id)}>
                        Сохранить ответ
                      </button>
                    </div>
                  </article>
                )) : <p className="muted">Отзывов пока нет.</p>}
              </div>
            </section>
          </>
        ) : null}
      </TrainerDashboardShell>
    </ProtectedPage>
  );
}
