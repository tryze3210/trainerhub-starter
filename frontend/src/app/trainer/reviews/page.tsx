'use client';

import { useEffect, useMemo, useState } from 'react';

import { ProtectedPage } from '@/components/protected-page';
import { TrainerDashboardShell } from '@/modules/trainer-dashboard/components/trainer-dashboard-shell';
import { reviewsApi, type Review, type TrainerReviewQuality } from '@/modules/reviews/api';

function formatDateTime(value?: string | null) {
  if (!value) return 'Дата не указана';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : new Intl.DateTimeFormat('ru-RU', { dateStyle: 'medium', timeStyle: 'short' }).format(date);
}

function shortId(value?: string | null) {
  if (!value) return 'ID не указан';
  return value.length > 10 ? `ID: ${value.slice(0, 6)}…${value.slice(-3)}` : `ID: ${value}`;
}

function mapContentTypeLabel(value?: string | null) {
  if (value === 'course') return 'Курс';
  if (value === 'program') return 'Программа';
  if (value === 'video') return 'Видео';
  if (value === 'product') return 'Продукт';
  if (value === 'lesson') return 'Урок';
  return 'Материал';
}

function mapReviewStatusLabel(value?: string | null) {
  if (value === 'published') return 'Опубликован';
  if (value === 'pending') return 'На модерации';
  if (value === 'rejected') return 'Отклонён';
  if (value === 'hidden') return 'Скрыт';
  if (value === 'flagged') return 'Требует внимания';
  return 'Требуется проверка';
}

function mapReadinessTone(value?: boolean) {
  return value ? 'success' : 'warning';
}

function getBadgeTone(value?: string | null) {
  if (value === 'published') return 'success';
  if (value === 'pending' || value === 'flagged') return 'warning';
  if (value === 'rejected' || value === 'hidden') return 'danger';
  return 'neutral';
}

function badgeClass(value?: string | null) {
  return `trainer-education-status trainer-education-status-${getBadgeTone(value)}`;
}

function readinessClass(isOk: boolean) {
  return `trainer-education-status trainer-education-status-${mapReadinessTone(isOk)}`;
}

function KpiCard({ label, value, hint }: { label: string; value: string | number; hint?: string }) {
  return (
    <article className="trainer-education-kpi-card">
      <span>{label}</span>
      <strong>{value}</strong>
      {hint ? <small>{hint}</small> : null}
    </article>
  );
}

function ReviewReply({ item, replyDrafts, setReplyDrafts, onSave }: {
  item: Review;
  replyDrafts: Record<string, string>;
  setReplyDrafts: (value: Record<string, string> | ((current: Record<string, string>) => Record<string, string>)) => void;
  onSave: (reviewId: string) => void;
}) {
  if (item.trainer_reply) {
    return (
      <div className="trainer-review-readiness-card">
        <span className="trainer-education-status trainer-education-status-success">Ответ тренера</span>
        <p>{item.trainer_reply}</p>
      </div>
    );
  }

  return (
    <div className="trainer-review-readiness-card">
      <label className="trainer-education-field">
        <span>Публичный ответ ученику</span>
        <textarea
          rows={3}
          value={replyDrafts[item.id] ?? ''}
          onChange={(event) => setReplyDrafts((current) => ({ ...current, [item.id]: event.target.value }))}
          placeholder="Поблагодарите ученика и ответьте по сути отзыва"
        />
      </label>
      <div className="trainer-education-actions">
        <button className="premium-secondary-button" type="button" onClick={() => onSave(item.id)}>
          Сохранить ответ
        </button>
      </div>
    </div>
  );
}

export default function TrainerReviewsPage() {
  const [payload, setPayload] = useState<TrainerReviewQuality | null>(null);
  const [replyDrafts, setReplyDrafts] = useState<Record<string, string>>({});
  const [msg, setMsg] = useState('');
  const [loading, setLoading] = useState(true);

  async function load() {
    try {
      setLoading(true);
      setMsg('');
      setPayload(await reviewsApi.getTrainerQuality(30));
    } catch (err) {
      setMsg(err instanceof Error ? err.message : 'Не удалось загрузить отзывы тренера');
    } finally {
      setLoading(false);
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

  const repliedCount = useMemo(
    () => payload?.recent_reviews.filter((item) => Boolean(item.trainer_reply)).length || 0,
    [payload?.recent_reviews]
  );

  return (
    <ProtectedPage title="Отзывы" description="Кабинет качества для тренера.">
      <TrainerDashboardShell
        title="Отзывы"
        description="Репутация, качество контента и публичные ответы ученикам."
      >
        <section className="trainer-review-workbench">
          <section className="trainer-review-hero">
            <div>
              <h2>Отзывы</h2>
              <p>Репутация, качество контента и публичные ответы ученикам.</p>
            </div>
            <div className="trainer-education-hero-total">
              <span>Средний рейтинг</span>
              <strong>{payload?.summary.average_rating || 0}/5</strong>
              <small>{payload?.summary.total_reviews || 0} отзывов · {payload?.summary.flagged_count || payload?.summary.low_rating_count || 0} требуют внимания</small>
            </div>
          </section>

          <div className="trainer-education-actions">
            <button className="premium-secondary-button" onClick={() => void load()} type="button">Обновить</button>
          </div>

          {msg ? <div className="trainer-education-message"><strong>Не удалось выполнить действие</strong><p>{msg}</p></div> : null}
          {loading ? <div className="trainer-education-message"><strong>Загружаем отзывы</strong><p>Получаем оценки, готовность к продажам и последние отзывы учеников.</p></div> : null}

          {payload ? (
            <>
              <section className="trainer-review-kpi-grid" aria-label="Показатели отзывов">
                <KpiCard label="Средний рейтинг" value={`${payload.summary.average_rating}/5`} />
                <KpiCard label="Всего отзывов" value={payload.summary.total_reviews} />
                <KpiCard label="Проблемные отзывы" value={payload.summary.flagged_count || payload.summary.low_rating_count} />
                <KpiCard label="Материалов с отзывами" value={payload.by_target.length} />
                <KpiCard label="Ответы тренера" value={repliedCount} />
              </section>

              <section className="trainer-review-layout">
                <div className="trainer-education-main">
                  <article className="trainer-review-card">
                    <h3>Контент по рейтингу</h3>
                    {payload.by_target.length ? payload.by_target.map((item) => (
                      <article className="trainer-review-readiness-card" key={`${item.target_type}-${item.target_id}`}>
                        <div className="trainer-education-row">
                          <div>
                            <strong>{item.target_title || shortId(item.target_id)}</strong>
                            <p>{mapContentTypeLabel(item.target_type)} · {item.reviews_count} отзывов</p>
                          </div>
                          <span className="trainer-education-status trainer-education-status-success">{item.average_rating}/5</span>
                        </div>
                        {!item.target_title ? <small className="trainer-education-muted">{shortId(item.target_id)}</small> : null}
                      </article>
                    )) : (
                      <div className="trainer-education-empty">
                        <strong>Оценок по материалам пока нет</strong>
                        <p>После первых отзывов здесь появится рейтинг контента.</p>
                      </div>
                    )}
                  </article>

                  <article className="trainer-review-card">
                    <h3>Последние отзывы</h3>
                    {payload.recent_reviews.length ? payload.recent_reviews.map((item) => (
                      <article className="trainer-review-readiness-card" key={item.id}>
                        <div className="trainer-education-row">
                          <div>
                            <strong>{item.title || 'Отзыв ученика'}</strong>
                            <p>{item.target_title || mapContentTypeLabel(item.target_type)} · {formatDateTime(item.created_at)}</p>
                          </div>
                          <span className={badgeClass(item.status)}>{mapReviewStatusLabel(item.status)}</span>
                        </div>
                        <p>{item.body}</p>
                        <ReviewReply item={item} replyDrafts={replyDrafts} setReplyDrafts={setReplyDrafts} onSave={(reviewId) => void saveReply(reviewId)} />
                      </article>
                    )) : (
                      <div className="trainer-education-empty">
                        <strong>Отзывов пока нет</strong>
                        <p>Отзывов пока нет. После первых покупок и оценок они появятся здесь.</p>
                      </div>
                    )}
                  </article>
                </div>

                <aside className="trainer-education-sidebar">
                  <article className="trainer-review-card">
                    <h3>Готовность к продажам</h3>
                    {payload.readiness.map((item) => (
                      <article className="trainer-review-readiness-card" key={item.code}>
                        <span className={readinessClass(item.is_ok)}>{item.is_ok ? 'Готово' : 'Требует внимания'}</span>
                        <strong>{item.label}</strong>
                      </article>
                    ))}
                  </article>
                </aside>
              </section>
            </>
          ) : null}
        </section>
      </TrainerDashboardShell>
    </ProtectedPage>
  );
}
