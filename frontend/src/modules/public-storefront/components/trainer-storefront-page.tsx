'use client';

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import {
  buildContentCheckoutHref,
  getStorefrontDescription,
  getStorefrontHref,
  getStorefrontPrice,
  publicStorefrontApi,
  type StorefrontItem,
} from '@/modules/public-storefront/api';
import type { TrainerProfile } from '@/types/api';

function metric(value?: number | string): string {
  if (value === undefined || value === null || value === '') return '0';
  return String(value);
}

function getTrainerItems(profile: TrainerProfile | null, catalog: StorefrontItem[]): StorefrontItem[] {
  if (!profile) return catalog;
  const embedded = Array.isArray(profile.catalog_items)
    ? profile.catalog_items.map((item) => ({
        id: item.id,
        slug: item.slug,
        title: item.title,
        description: item.description,
        category: item.category,
        difficulty: item.difficulty,
        price_amount: item.price,
        price: item.price,
        currency: item.currency,
        duration_minutes: item.duration_minutes,
        trainer_slug: item.trainer_slug,
        trainer_name: item.trainer_name,
        is_featured: item.is_featured,
        entity_type: (item.entity_type === 'program' || item.entity_type === 'bundle' ? item.entity_type : 'video') as StorefrontItem['entity_type'],
      }))
    : [];

  if (embedded.length > 0) return embedded;
  return catalog.filter((item) => item.trainer_slug === profile.slug);
}

export function TrainerStorefrontPage({ slug }: { slug: string }) {
  const [profile, setProfile] = useState<TrainerProfile | null>(null);
  const [catalog, setCatalog] = useState<StorefrontItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let mounted = true;

    async function load() {
      try {
        setLoading(true);
        setError('');
        const [trainer, scopedCatalog] = await Promise.all([
          publicStorefrontApi.getTrainer(slug),
          publicStorefrontApi.listCatalog({ trainerSlug: slug }),
        ]);
        if (mounted) {
          setProfile(trainer);
          setCatalog(scopedCatalog);
        }
      } catch (err) {
        if (mounted) setError(err instanceof Error ? err.message : 'Профиль тренера недоступен');
      } finally {
        if (mounted) setLoading(false);
      }
    }

    void load();
    return () => {
      mounted = false;
    };
  }, [slug]);

  const items = useMemo(() => getTrainerItems(profile, catalog), [catalog, profile]);
  const featured = items.filter((item) => item.is_featured).slice(0, 3);

  if (loading) {
    return (
      <main className="page-shell stack">
        <section className="card stack">
          <span className="badge">Загрузка</span>
          <h1>Получаем storefront тренера...</h1>
          <p>Загружаем публичный профиль, продукты и social proof.</p>
        </section>
      </main>
    );
  }

  if (error || !profile) {
    return (
      <main className="page-shell stack">
        <section className="card stack danger">
          <h1>Тренер недоступен</h1>
          <p>{error || 'Не удалось получить публичный профиль.'}</p>
          <Link className="btn" href="/trainers">Вернуться к тренерам</Link>
        </section>
      </main>
    );
  }

  return (
    <main className="page-shell stack">
      <section className="hero card stack">
        <span className="eyebrow">Trainer storefront</span>
        <h1>{profile.display_name}</h1>
        <p>{profile.headline || profile.bio || 'Тренер пока не заполнил публичное позиционирование.'}</p>
        <div className="actions compact">
          {(profile.specialties || []).slice(0, 5).map((tag) => (
            <span className="badge" key={tag}>{tag}</span>
          ))}
          {(profile.languages || []).slice(0, 3).map((lang) => (
            <span className="badge" key={lang}>{lang}</span>
          ))}
        </div>
        <div className="actions">
          <Link className="btn btn-primary" href="#trainer-products">
            Смотреть продукты
          </Link>
          <Link className="btn" href="/subscriptions">
            Подписка
          </Link>
        </div>
      </section>

      <section className="grid-4">
        <article className="card stack compact">
          <span className="muted">Rating</span>
          <strong>{metric(profile.rating ?? profile.rating_avg)}</strong>
        </article>
        <article className="card stack compact">
          <span className="muted">Reviews</span>
          <strong>{metric(profile.reviews_count)}</strong>
        </article>
        <article className="card stack compact">
          <span className="muted">Students</span>
          <strong>{metric(profile.students_count)}</strong>
        </article>
        <article className="card stack compact">
          <span className="muted">Products</span>
          <strong>{metric(profile.active_products_count || items.length)}</strong>
        </article>
      </section>

      <section className="grid-2">
        <article className="card stack">
          <span className="eyebrow">About</span>
          <h2>О тренере</h2>
          <p>{profile.bio || 'Подробное описание пока не заполнено.'}</p>
        </article>
        <article className="card stack">
          <span className="eyebrow">Buyer trust</span>
          <h2>Почему это готово к продаже</h2>
          <ul>
            <li>Профиль проходит trainer onboarding и admin review.</li>
            <li>Контент покупается через единый checkout/order flow.</li>
            <li>Доступы проверяются через entitlement/access center.</li>
          </ul>
        </article>
      </section>

      {featured.length > 0 ? (
        <section className="stack">
          <div className="section-heading">
            <div>
              <span className="eyebrow">Featured</span>
              <h2>Рекомендуемые продукты тренера</h2>
            </div>
          </div>
          <div className="grid-3">
            {featured.map((item) => (
              <article className="card stack" key={`featured:${item.entity_type}:${item.id}`}>
                <span className="badge">{item.entity_type}</span>
                <h3>{item.title}</h3>
                <p>{getStorefrontDescription(item)}</p>
                <strong>{getStorefrontPrice(item)}</strong>
                <Link className="btn btn-primary" href={getStorefrontHref(item)}>
                  Подробнее
                </Link>
              </article>
            ))}
          </div>
        </section>
      ) : null}

      <section className="stack" id="trainer-products">
        <div className="section-heading">
          <div>
            <span className="eyebrow">Storefront catalog</span>
            <h2>Продукты тренера</h2>
          </div>
          <span className="badge">{items.length} items</span>
        </div>

        {items.length === 0 ? (
          <article className="card stack">
            <h3>Пока нет опубликованных продуктов</h3>
            <p>Когда тренер опубликует видео, программы или bundles, они появятся здесь.</p>
          </article>
        ) : (
          <div className="grid-3">
            {items.map((item) => (
              <article className="card stack" key={`${item.entity_type}:${item.id}`}>
                <div className="section-heading">
                  <span className="badge">{item.entity_type}</span>
                  <strong>{getStorefrontPrice(item)}</strong>
                </div>
                <h3>{item.title}</h3>
                <p>{getStorefrontDescription(item)}</p>
                <div className="actions">
                  <Link className="btn btn-primary" href={getStorefrontHref(item)}>
                    Открыть
                  </Link>
                  <Link className="btn" href={buildContentCheckoutHref(item)}>
                    Купить
                  </Link>
                </div>
              </article>
            ))}
          </div>
        )}
      </section>
    </main>
  );
}
