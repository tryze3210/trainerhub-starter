'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useEffect, useState } from 'react';
import { StorefrontCheckoutCard } from '@/components/storefront-checkout-card';
import { StorefrontReviewsPanel } from '@/components/storefront-reviews-panel';
import { publicApi } from '@/lib/api';
import type { PublicVideo } from '@/types/api';

export default function VideoDetailPage() {
  const params = useParams<{ slug: string }>();
  const slug = params?.slug || '';
  const [item, setItem] = useState<PublicVideo | null>(null);
  const [msg, setMsg] = useState('');

  useEffect(() => {
    if (!slug) return;
    void (async () => {
      try {
        setMsg('');
        const payload = await publicApi.getVideo(slug);
        setItem(payload);
      } catch (err) {
        setMsg(err instanceof Error ? err.message : 'Не удалось загрузить видео');
      }
    })();
  }, [slug]);

  if (msg) return <div className="card error">{msg}</div>;
  if (!item) return <div className="card">Загрузка видео...</div>;

  return (
    <section className="grid-layout-detail">
      <div className="stack" style={{ gap: 20 }}>
        <div className="card dark">
          <span className="badge">Видео</span>
          <h1 className="title-lg">{item.title}</h1>
          <p className="lead">{item.description}</p>
          <div className="inline">
            <Link href={`/trainers/${item.trainer_slug}`} className="button secondary">Тренер: {item.trainer_name}</Link>
            <span className="badge secondary">{item.duration_minutes || 0} мин</span>
          </div>
        </div>
        <StorefrontReviewsPanel targetType="video" targetId={item.id} />
      </div>
      <StorefrontCheckoutCard itemType="video" itemId={item.id} title={item.title} amount={item.price_amount} currency={item.currency} />
    </section>
  );
}
