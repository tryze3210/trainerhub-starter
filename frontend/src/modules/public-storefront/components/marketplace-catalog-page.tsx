'use client';

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import { DSBadge, DSEmptyState, DSPageHeader, DSSection, DSSelect, DSSkeleton, DSTextField, DSTransitionPanel } from '@/design-system';
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
      <DSPageHeader
        eyebrow="TrainerHub marketplace"
        title="Каталог видео, программ и bundle-предложений"
        description="Публичная витрина показывает коммерческие карточки: тип контента, цену, тренера, уровень, duration и явный CTA на покупку или подписку."
        actions={
          <>
            <Link className="btn btn-primary" href="/trainers">Смотреть тренеров</Link>
            <Link className="btn" href="/subscriptions">Подписки</Link>
          </>
        }
      />

      <DSSection title="Фильтры каталога" description="Поиск по названию, тренеру, категории, уровню и типу контента." actions={<DSBadge>{filtered.length} items</DSBadge>}>
        <div className="card compact stack">
          <span className="badge secondary">Discovery</span>
        <div className="grid-2">
          <DSTextField
            label="Поиск"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Йога, силовая, марафон, имя тренера..."
          />
          <DSSelect label="Тип контента" value={type} onChange={(event) => setType(event.target.value as 'all' | StorefrontEntityType)}>
              <option value="all">Все</option>
              <option value="video">Видео</option>
              <option value="program">Программы</option>
              <option value="bundle">Bundles</option>
          </DSSelect>
          </div>
        </div>
      </DSSection>

      {featured.length > 0 ? (
        <DSSection title="Выделенные предложения" description="Featured marketplace items.">
          <DSTransitionPanel active>
          <div className="grid-3">
            {featured.map((item) => (
              <article className="card stack" key={`${item.entity_type}:${item.id}:featured`}>
                <DSBadge>{TYPE_LABELS[item.entity_type]}</DSBadge>
                <h3>{item.title}</h3>
                <p>{getStorefrontDescription(item)}</p>
                <strong>{getStorefrontPrice(item)}</strong>
                <Link className="btn btn-primary" href={getStorefrontHref(item)}>
                  Открыть
                </Link>
              </article>
            ))}
          </div>
          </DSTransitionPanel>
        </DSSection>
      ) : null}

      <DSSection title="Все предложения" description="Каталог видео, программ и bundles.">
        <span className="badge secondary">Catalog</span>

        {error ? <div className="card danger">{error}</div> : null}

        {loading ? (
          <div className="grid-3">
            {Array.from({ length: 6 }).map((_, index) => (
              <article className="card" key={index}>
                <DSSkeleton lines={4} />
              </article>
            ))}
          </div>
        ) : filtered.length === 0 ? (
          <DSEmptyState title="Ничего не найдено" description="Измени поиск или фильтр типа контента." />
        ) : (
          <DSTransitionPanel active className="grid-3">
            {filtered.map((item) => (
              <article className="card stack" key={`${item.entity_type}:${item.id}`}>
                <div className="section-heading">
                  <DSBadge>{TYPE_LABELS[item.entity_type]}</DSBadge>
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
          </DSTransitionPanel>
        )}
      </DSSection>
    </main>
  );
}
