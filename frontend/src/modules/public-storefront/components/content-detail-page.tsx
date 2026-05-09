'use client';

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import {
  buildContentCheckoutHref,
  getStorefrontDescription,
  getStorefrontPrice,
  publicStorefrontApi,
  type StorefrontEntityType,
  type StorefrontItem,
} from '@/modules/public-storefront/api';
import type { PublicBundle, PublicProgram, PublicVideo } from '@/types/api';

const TYPE_LABELS: Record<StorefrontEntityType, string> = {
  video: 'Видео',
  program: 'Программа',
  bundle: 'Bundle',
};

function toStorefrontItem(
  payload: PublicVideo | PublicProgram | PublicBundle,
  entityType: StorefrontEntityType
): StorefrontItem {
  return {
    ...payload,
    entity_type: entityType,
    price: payload.price_amount,
  };
}

function lessonsCount(item: Partial<PublicProgram | PublicBundle>): number {
  const lessons = (item as PublicProgram).lessons;
  const bundleItems = (item as PublicBundle).items;
  if (Array.isArray(lessons)) return lessons.length;
  if (Array.isArray(bundleItems)) return bundleItems.length;
  return 0;
}

export function ContentDetailPage({ type, slug }: { type: StorefrontEntityType; slug: string }) {
  const [item, setItem] = useState<StorefrontItem | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let mounted = true;

    async function load() {
      try {
        setLoading(true);
        setError('');
        if (type === 'video') {
          const payload = await publicStorefrontApi.getVideo(slug);
          if (mounted) setItem(toStorefrontItem(payload, 'video'));
        } else if (type === 'program') {
          const payload = await publicStorefrontApi.getProgram(slug);
          if (mounted) setItem(toStorefrontItem(payload, 'program'));
        } else {
          const payload = await publicStorefrontApi.getBundle(slug);
          if (mounted) setItem(toStorefrontItem(payload, 'bundle'));
        }
      } catch (err) {
        if (mounted) setError(err instanceof Error ? err.message : 'Контент недоступен');
      } finally {
        if (mounted) setLoading(false);
      }
    }

    void load();
    return () => {
      mounted = false;
    };
  }, [slug, type]);

  const checkoutHref = useMemo(() => (item ? buildContentCheckoutHref(item) : '/login'), [item]);

  if (loading) {
    return (
      <main className="page-shell stack">
        <section className="card stack">
          <span className="badge">Загрузка</span>
          <h1>Получаем страницу контента...</h1>
          <p>Загружаем описание, цену и trainer attribution.</p>
        </section>
      </main>
    );
  }

  if (error || !item) {
    return (
      <main className="page-shell stack">
        <section className="card stack danger">
          <h1>Контент недоступен</h1>
          <p>{error || 'Не удалось получить публичную карточку.'}</p>
          <Link className="btn" href="/catalog">Вернуться в каталог</Link>
        </section>
      </main>
    );
  }

  return (
    <main className="page-shell stack">
      <section className="hero card stack">
        <span className="eyebrow">{TYPE_LABELS[type]} · public offer</span>
        <h1>{item.title}</h1>
        <p>{getStorefrontDescription(item)}</p>
        <div className="actions">
          <Link className="btn btn-primary" href={checkoutHref}>
            Купить за {getStorefrontPrice(item)}
          </Link>
          <Link className="btn" href="/subscriptions">
            Смотреть подписки
          </Link>
          {item.trainer_slug ? (
            <Link className="btn" href={`/trainers/${item.trainer_slug}`}>
              Тренер: {item.trainer_name || item.trainer_slug}
            </Link>
          ) : null}
        </div>
      </section>

      <section className="grid-4">
        <article className="card stack compact">
          <span className="muted">Цена</span>
          <strong>{getStorefrontPrice(item)}</strong>
        </article>
        <article className="card stack compact">
          <span className="muted">Уровень</span>
          <strong>{item.difficulty || 'любой'}</strong>
        </article>
        <article className="card stack compact">
          <span className="muted">Категория</span>
          <strong>{item.category || 'общая'}</strong>
        </article>
        <article className="card stack compact">
          <span className="muted">Длительность</span>
          <strong>{item.duration_minutes ? `${item.duration_minutes} мин` : '—'}</strong>
        </article>
      </section>

      <section className="grid-2">
        <article className="card stack">
          <span className="eyebrow">What buyer gets</span>
          <h2>Что получает покупатель</h2>
          <ul>
            <li>Доступ к выбранному {TYPE_LABELS[type].toLowerCase()} после успешной оплаты.</li>
            <li>Доступ отображается в личном кабинете и access center.</li>
            <li>Платёж проходит через checkout/order integrity слой.</li>
          </ul>
        </article>
        <article className="card stack">
          <span className="eyebrow">Commercial metadata</span>
          <h2>Параметры предложения</h2>
          <div className="stack compact">
            <span>Slug: {item.slug}</span>
            <span>Trainer: {item.trainer_name || 'TrainerHub'}</span>
            <span>Items/Lessons: {lessonsCount(item)}</span>
            <span>Featured: {item.is_featured ? 'yes' : 'no'}</span>
          </div>
        </article>
      </section>
    </main>
  );
}
