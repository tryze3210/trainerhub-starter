'use client';

export const dynamic = 'force-dynamic';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useEffect, useState } from 'react';
import { StorefrontReviewsPanel } from '@/components/storefront-reviews-panel';
import { publicApi } from '@/lib/api';
import type { TrainerProfile } from '@/types/api';

export default function TrainerProfilePage() {
  const params = useParams<{ slug: string }>();
  const slug = params?.slug ?? '';
  const [trainer, setTrainer] = useState<TrainerProfile | null>(null);
  const [msg, setMsg] = useState('');

  useEffect(() => {
    if (!slug) return;

    void (async () => {
      try {
        setMsg('');
        const payload = await publicApi.getTrainer(slug);
        setTrainer(payload);
      } catch (err) {
        setMsg(err instanceof Error ? err.message : 'Не удалось загрузить профиль тренера');
      }
    })();
  }, [slug]);

  if (msg) return <div className="card error">{msg}</div>;
  if (!trainer) return <div className="card">Загрузка профиля тренера...</div>;

  return (
    <section className="stack" style={{ gap: 24 }}>
      <div className="card dark">
        <div className="stack" style={{ gap: 12 }}>
          <span className="badge success">Публичный профиль</span>
          <h1>{trainer.display_name}</h1>
          <p className="lead">{trainer.headline || 'Headline пока не заполнен.'}</p>
          <p>{trainer.bio || 'Биография тренера пока не заполнена.'}</p>
          <div className="inline">
            <span className="badge secondary">Рейтинг: {trainer.rating ?? trainer.rating_avg ?? '0.0'}</span>
            <span className="badge secondary">Отзывы: {trainer.reviews_count || 0}</span>
            <span className="badge secondary">Продуктов: {trainer.active_products_count || 0}</span>
          </div>
        </div>
      </div>

      {trainer.catalog_items?.length ? (
        <div className="card">
          <h3 className="title-md">Витрина тренера</h3>
          <div className="grid-2" style={{ marginTop: 16 }}>
            {trainer.catalog_items.map((item) => (
              <article key={`${item.entity_type}-${item.id}`} className="card compact">
                <span className="badge">{item.entity_type}</span>
                <h4 style={{ marginTop: 10 }}>{item.title}</h4>
                <p className="muted">{item.description}</p>
                <div className="row" style={{ marginTop: 12 }}>
                  <span className="price">{item.price || '—'} {item.currency || 'RUB'}</span>
                  <Link href={`/catalog/${item.entity_type}s/${item.slug}`} className="button secondary">Открыть</Link>
                </div>
              </article>
            ))}
          </div>
        </div>
      ) : null}

      <StorefrontReviewsPanel targetType="trainer" targetId={trainer.slug} />

      <div className="inline">
        <Link href="/trainers" className="button secondary">Назад в каталог</Link>
        <Link href="/catalog" className="button ghost">Перейти к контенту</Link>
      </div>
    </section>
  );
}
