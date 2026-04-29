'use client';

export const dynamic = 'force-dynamic';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { publicApi } from '@/lib/api';
import type { TrainerProfile } from '@/types/api';

function metric(value?: number | string) {
  if (value === undefined || value === null || value === '') return '0';
  return String(value);
}

export default function TrainersPage() {
  const [list, setList] = useState<TrainerProfile[]>([]);
  const [msg, setMsg] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    void (async () => {
      try {
        setLoading(true);
        setMsg('');
        const trainers = await publicApi.listTrainers();
        setList(trainers);
      } catch (err) {
        setMsg(err instanceof Error ? err.message : 'Ошибка загрузки тренеров');
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  return (
    <section className="stack" style={{ gap: 24 }}>
      <div className="trainers-hero card dark">
        <div className="stack" style={{ gap: 12 }}>
          <span className="badge success">Public marketplace</span>
          <h1>Каталог тренеров</h1>
          <p className="lead">
            Это уже не просто список аккаунтов. Здесь начинает собираться настоящая marketplace-витрина:
            позиционирование, social proof и активные продукты тренера.
          </p>
        </div>
      </div>

      {msg ? (
        <div className="card error">{msg}</div>
      ) : loading ? (
        <div className="grid-3">
          {Array.from({ length: 6 }).map((_, idx) => (
            <div key={idx} className="card trainer-card">
              <div className="stack" style={{ gap: 10 }}>
                <span className="badge secondary">Загрузка</span>
                <p className="muted">Получаем список тренеров…</p>
              </div>
            </div>
          ))}
        </div>
      ) : list.length === 0 ? (
        <div className="empty-state">
          <h3>Публичных тренеров пока нет</h3>
          <p>Когда профили станут публичными и появится контент, они появятся в этом каталоге.</p>
        </div>
      ) : (
        <div className="grid-3">
          {list.map((trainer) => (
            <article key={trainer.id} className="card trainer-card">
              <div className="stack" style={{ gap: 14 }}>
                <div className="inline" style={{ justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div className="stack" style={{ gap: 6 }}>
                    <span className="badge success">Public profile</span>
                    <h3 style={{ margin: 0 }}>{trainer.display_name}</h3>
                  </div>
                  <div className="trainer-avatar-fallback" aria-hidden="true">
                    {trainer.display_name.slice(0, 1).toUpperCase()}
                  </div>
                </div>

                <p className="muted">{trainer.headline || 'Headline пока не заполнен.'}</p>
                <p>{trainer.bio || 'Описание тренера пока не заполнено.'}</p>

                <div className="trainer-card__tags">
                  {(trainer.specialties || []).slice(0, 3).map((tag) => (
                    <span key={tag} className="badge secondary">{tag}</span>
                  ))}
                  {(trainer.languages || []).slice(0, 2).map((lang) => (
                    <span key={lang} className="badge ghost">{lang}</span>
                  ))}
                </div>

                <div className="trainer-card__metrics">
                  <div>
                    <span className="muted">Rating</span>
                    <strong>{metric(trainer.rating ?? trainer.rating_avg)}</strong>
                  </div>
                  <div>
                    <span className="muted">Reviews</span>
                    <strong>{metric(trainer.reviews_count)}</strong>
                  </div>
                  <div>
                    <span className="muted">Students</span>
                    <strong>{metric(trainer.students_count)}</strong>
                  </div>
                  <div>
                    <span className="muted">Products</span>
                    <strong>{metric(trainer.active_products_count)}</strong>
                  </div>
                </div>

                <Link href={`/trainers/${trainer.slug}`} className="button">Открыть storefront</Link>
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
