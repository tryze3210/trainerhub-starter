'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useEffect, useState } from 'react';
import { StorefrontCheckoutCard } from '@/components/storefront-checkout-card';
import { StorefrontReviewsPanel } from '@/components/storefront-reviews-panel';
import { publicApi } from '@/lib/api';
import type { PublicBundle } from '@/types/api';

export default function BundleDetailPage() {
  const params = useParams<{ slug: string }>();
  const slug = params?.slug || '';
  const [item, setItem] = useState<PublicBundle | null>(null);
  const [msg, setMsg] = useState('');

  useEffect(() => {
    if (!slug) return;
    void (async () => {
      try {
        setMsg('');
        const payload = await publicApi.getBundle(slug);
        setItem(payload);
      } catch (err) {
        setMsg(err instanceof Error ? err.message : 'Не удалось загрузить bundle');
      }
    })();
  }, [slug]);

  if (msg) return <div className="card error">{msg}</div>;
  if (!item) return <div className="card">Загрузка bundle...</div>;

  return (
    <section className="grid-layout-detail">
      <div className="stack" style={{ gap: 20 }}>
        <div className="card dark">
          <span className="badge">Bundle</span>
          <h1 className="title-lg">{item.title}</h1>
          <p className="lead">{item.description}</p>
          <div className="inline">
            <Link href={`/trainers/${item.trainer_slug}`} className="button secondary">Тренер: {item.trainer_name}</Link>
            <span className="badge secondary">Элементов: {item.items?.length || 0}</span>
          </div>
        </div>
        {item.items?.length ? (
          <div className="card">
            <h3 className="title-md">Что входит в bundle</h3>
            <div className="stack" style={{ gap: 10, marginTop: 14 }}>
              {item.items.map((bundleItem, index) => (
                <div key={bundleItem.id} className="card compact">
                  <strong>{index + 1}. {bundleItem.target_title || bundleItem.target_slug || bundleItem.item_type}</strong>
                  <p className="muted">Тип: {bundleItem.item_type}</p>
                </div>
              ))}
            </div>
          </div>
        ) : null}
        <StorefrontReviewsPanel targetType="bundle" targetId={item.id} />
      </div>
      <StorefrontCheckoutCard itemType="bundle" itemId={item.id} title={item.title} amount={item.price_amount} currency={item.currency} />
    </section>
  );
}
