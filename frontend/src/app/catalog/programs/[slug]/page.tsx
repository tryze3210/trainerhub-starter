'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useEffect, useState } from 'react';
import { StorefrontCheckoutCard } from '@/components/storefront-checkout-card';
import { StorefrontReviewsPanel } from '@/components/storefront-reviews-panel';
import { publicApi } from '@/lib/api';
import type { PublicProgram } from '@/types/api';

export default function ProgramDetailPage() {
  const params = useParams<{ slug: string }>();
  const slug = params?.slug || '';
  const [item, setItem] = useState<PublicProgram | null>(null);
  const [msg, setMsg] = useState('');

  useEffect(() => {
    if (!slug) return;
    void (async () => {
      try {
        setMsg('');
        const payload = await publicApi.getProgram(slug);
        setItem(payload);
      } catch (err) {
        setMsg(err instanceof Error ? err.message : 'Не удалось загрузить программу');
      }
    })();
  }, [slug]);

  if (msg) return <div className="card error">{msg}</div>;
  if (!item) return <div className="card">Загрузка программы...</div>;

  return (
    <section className="grid-layout-detail">
      <div className="stack" style={{ gap: 20 }}>
        <div className="card dark">
          <span className="badge">Программа</span>
          <h1 className="title-lg">{item.title}</h1>
          <p className="lead">{item.description}</p>
          <div className="inline">
            <Link href={`/trainers/${item.trainer_slug}`} className="button secondary">Тренер: {item.trainer_name}</Link>
            <span className="badge secondary">Уроков: {item.lessons?.length || 0}</span>
          </div>
        </div>
        {item.lessons?.length ? (
          <div className="card">
            <h3 className="title-md">Состав программы</h3>
            <div className="stack" style={{ gap: 10, marginTop: 14 }}>
              {item.lessons.map((lesson, index) => (
                <div key={lesson.id} className="card compact">
                  <strong>{index + 1}. {lesson.title}</strong>
                  <p className="muted">{lesson.description || 'Описание урока пока не заполнено.'}</p>
                </div>
              ))}
            </div>
          </div>
        ) : null}
        <StorefrontReviewsPanel targetType="program" targetId={item.id} />
      </div>
      <StorefrontCheckoutCard itemType="program" itemId={item.id} title={item.title} amount={item.price_amount} currency={item.currency} />
    </section>
  );
}
