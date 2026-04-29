'use client';

import { useEffect, useState } from 'react';
import { useAuthSession } from '@/components/auth-provider';
import { reviewsApi, type ReviewPayload } from '@/modules/reviews/api';

export function StorefrontReviewsPanel({ targetType, targetId }: { targetType: string; targetId: string }) {
  const { isAuthenticated } = useAuthSession();
  const [payload, setPayload] = useState<ReviewPayload | null>(null);
  const [rating, setRating] = useState(5);
  const [title, setTitle] = useState('');
  const [body, setBody] = useState('');
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [msg, setMsg] = useState('');

  async function load() {
    try {
      setLoading(true);
      setMsg('');
      const data = await reviewsApi.getTargetReviews(targetType, targetId);
      setPayload(data);
      if (data.viewer_review) {
        setRating(data.viewer_review.rating);
        setTitle(data.viewer_review.title);
        setBody(data.viewer_review.body);
      }
    } catch (err) {
      setMsg(err instanceof Error ? err.message : 'Не удалось загрузить отзывы');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, [targetId, targetType]);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    try {
      setSubmitting(true);
      setMsg('');
      await reviewsApi.createReview(targetType, targetId, { rating, title, body });
      await load();
      setMsg('Отзыв отправлен на модерацию. После публикации он появится на витрине.');
    } catch (err) {
      setMsg(err instanceof Error ? err.message : 'Не удалось отправить отзыв');
    } finally {
      setSubmitting(false);
    }
  }

  const eligibility = payload?.eligibility;
  const canReview = Boolean(isAuthenticated && eligibility?.can_review);

  return (
    <section className="card">
      <div className="stack" style={{ gap: 18 }}>
        <div className="row" style={{ alignItems: 'flex-start' }}>
          <div className="stack" style={{ gap: 8 }}>
            <span className="badge secondary">Отзывы</span>
            <h3 className="title-md">Отзывы и рейтинг</h3>
            <p className="muted">
              Средняя оценка: <strong>{payload?.summary.average_rating ?? 0}</strong> · Отзывов: <strong>{payload?.summary.reviews_count ?? 0}</strong>
            </p>
          </div>
          {eligibility?.verified_purchase ? <span className="badge success">Проверенная покупка</span> : null}
        </div>

        {msg ? <div className="card compact">{msg}</div> : null}

        {isAuthenticated ? (
          canReview ? (
            <form className="form" onSubmit={handleSubmit}>
              <div className="grid-2">
                <div className="form-group">
                  <label className="label" htmlFor={`rating-${targetType}-${targetId}`}>Оценка</label>
                  <select id={`rating-${targetType}-${targetId}`} className="select" value={rating} onChange={(e) => setRating(Number(e.target.value))}>
                    {[5, 4, 3, 2, 1].map((value) => (
                      <option key={value} value={value}>{value}</option>
                    ))}
                  </select>
                </div>
                <div className="form-group">
                  <label className="label" htmlFor={`title-${targetType}-${targetId}`}>Заголовок</label>
                  <input id={`title-${targetType}-${targetId}`} className="input" value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Короткий итог" required />
                </div>
              </div>
              <div className="form-group">
                <label className="label" htmlFor={`body-${targetType}-${targetId}`}>Текст отзыва</label>
                <textarea id={`body-${targetType}-${targetId}`} className="textarea" value={body} onChange={(e) => setBody(e.target.value)} rows={4} placeholder="Что понравилось, что можно улучшить" required />
              </div>
              {payload?.viewer_review ? (
                <p className="muted">Текущий статус твоего отзыва: <strong>{payload.viewer_review.status}</strong></p>
              ) : null}
              <button className="button" type="submit" disabled={submitting}>{submitting ? 'Отправляем...' : 'Отправить отзыв'}</button>
            </form>
          ) : (
            <div className="card compact">
              <strong>Отзыв доступен после покупки.</strong>
              <p className="muted" style={{ marginTop: 6 }}>{eligibility?.reason || 'Нужен активный доступ к этому материалу.'}</p>
            </div>
          )
        ) : (
          <div className="card compact">Войди в аккаунт, чтобы оставить отзыв после покупки материала.</div>
        )}

        {loading ? (
          <div className="muted">Загрузка отзывов...</div>
        ) : payload?.items?.length ? (
          <div className="stack" style={{ gap: 12 }}>
            {payload.items.map((item) => (
              <article key={item.id} className="card compact">
                <div className="row" style={{ alignItems: 'flex-start' }}>
                  <div className="stack" style={{ gap: 6 }}>
                    <strong>{item.title}</strong>
                    <span className="muted">{item.author_name} · {item.rating}/5</span>
                  </div>
                  <div className="inline">
                    {item.verified_purchase ? <span className="badge success">verified</span> : null}
                    <span className="badge secondary">{item.created_at ? new Date(item.created_at).toLocaleDateString('ru-RU') : '—'}</span>
                  </div>
                </div>
                <p style={{ marginTop: 10 }}>{item.body}</p>
              </article>
            ))}
          </div>
        ) : (
          <div className="empty-state">
            <h4>Отзывов пока нет</h4>
            <p>Первые отзывы появятся после покупок и модерации.</p>
          </div>
        )}
      </div>
    </section>
  );
}
