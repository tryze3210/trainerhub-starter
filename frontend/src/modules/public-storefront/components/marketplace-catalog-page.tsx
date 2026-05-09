'use client';

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import {
  buildContentCheckoutHref,
  getStorefrontDescription,
  getStorefrontHref,
  getStorefrontPrice,
  publicStorefrontApi,
  type StorefrontEntityType,
  type StorefrontItem,
} from '@/modules/public-storefront/api';

const TYPE_LABELS: Record<StorefrontEntityType, string> = {
  video: 'Видео',
  program: 'Программа',
  bundle: 'Bundle',
};

function metric(value: number | string | undefined): string {
  if (value === undefined || value === null || value === '') return '—';
  return String(value);
}

export function MarketplaceCatalogPage() {
  const [items, setItems] = useState<StorefrontItem[]>([]);
  const [query, setQuery] = useState('');
  const [type, setType] = useState<'all' | StorefrontEntityType>('all');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let mounted = true;

    async function load() {
      try {
        setLoading(true);
        setError('');
        const catalog = await publicStorefrontApi.listCatalog();
        if (mounted) setItems(catalog);
      } catch (err) {
        if (mounted) setError(err instanceof Error ? err.message : 'Не удалось загрузить каталог');
      } finally {
        if (mounted) setLoading(false);
      }
    }

    void load();
    return () => {
      mounted = false;
    };
  }, []);

  const filtered = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    return items.filter((item) => {
      const matchesType = type === 'all' || item.entity_type === type;
      const haystack = [
        item.title,
        item.description,
        item.category,
        item.difficulty,
        item.trainer_name,
        item.entity_type,
      ]
        .filter(Boolean)
        .join(' ')
        .toLowerCase();
      return matchesType && (normalized ? haystack.includes(normalized) : true);
    });
  }, [items, query, type]);

  const featured = filtered.filter((item) => item.is_featured).slice(0, 3);

  return (
    <main className="stack page-shell">
      <section className="hero card stack">
        <span className="eyebrow">TrainerHub marketplace</span>
        <h1>Каталог видео, программ и bundle-предложений</h1>
        <p>
          Публичная витрина теперь показывает коммерческие карточки: тип контента, цену, тренера,
          уровень, duration и явный CTA на покупку или подписку.
        </p>
        <div className="actions">
          <Link className="btn btn-primary" href="/trainers">
            Смотреть тренеров
          </Link>
          <Link className="btn" href="/subscriptions">
            Подписки
          </Link>
        </div>
      </section>

      <section className="card stack">
        <div className="section-heading">
          <div>
            <span className="eyebrow">Discovery</span>
            <h2>Фильтры каталога</h2>
          </div>
          <span className="badge">{filtered.length} items</span>
        </div>
        <div className="grid-2">
          <label className="stack compact">
            <span className="muted">Поиск</span>
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Йога, силовая, марафон, имя тренера..."
            />
          </label>
          <label className="stack compact">
            <span className="muted">Тип контента</span>
            <select value={type} onChange={(event) => setType(event.target.value as 'all' | StorefrontEntityType)}>
              <option value="all">Все</option>
              <option value="video">Видео</option>
              <option value="program">Программы</option>
              <option value="bundle">Bundles</option>
            </select>
          </label>
        </div>
      </section>

      {featured.length > 0 ? (
        <section className="stack">
          <div className="section-heading">
            <div>
              <span className="eyebrow">Featured</span>
              <h2>Выделенные предложения</h2>
            </div>
          </div>
          <div className="grid-3">
            {featured.map((item) => (
              <article className="card stack" key={`${item.entity_type}:${item.id}:featured`}>
                <span className="badge">{TYPE_LABELS[item.entity_type]}</span>
                <h3>{item.title}</h3>
                <p>{getStorefrontDescription(item)}</p>
                <strong>{getStorefrontPrice(item)}</strong>
                <Link className="btn btn-primary" href={getStorefrontHref(item)}>
                  Открыть
                </Link>
              </article>
            ))}
          </div>
        </section>
      ) : null}

      <section className="stack">
        <div className="section-heading">
          <div>
            <span className="eyebrow">Catalog</span>
            <h2>Все предложения</h2>
          </div>
        </div>

        {error ? <div className="card danger">{error}</div> : null}

        {loading ? (
          <div className="grid-3">
            {Array.from({ length: 6 }).map((_, index) => (
              <article className="card stack" key={index}>
                <span className="badge">Загрузка</span>
                <h3>Получаем контент...</h3>
                <p>Собираем публичные видео, программы и bundles.</p>
              </article>
            ))}
          </div>
        ) : filtered.length === 0 ? (
          <div className="card stack">
            <h3>Ничего не найдено</h3>
            <p>Измени поиск или фильтр типа контента.</p>
          </div>
        ) : (
          <div className="grid-3">
            {filtered.map((item) => (
              <article className="card stack" key={`${item.entity_type}:${item.id}`}>
                <div className="section-heading">
                  <span className="badge">{TYPE_LABELS[item.entity_type]}</span>
                  <strong>{getStorefrontPrice(item)}</strong>
                </div>
                <h3>{item.title}</h3>
                <p>{getStorefrontDescription(item)}</p>
                <div className="grid-2 compact">
                  <span className="muted">Тренер: {item.trainer_name || 'TrainerHub'}</span>
                  <span className="muted">Длительность: {metric(item.duration_minutes)} мин</span>
                  <span className="muted">Уровень: {item.difficulty || 'любой'}</span>
                  <span className="muted">Категория: {item.category || 'общая'}</span>
                </div>
                <div className="actions">
                  <Link className="btn btn-primary" href={getStorefrontHref(item)}>
                    Подробнее
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
