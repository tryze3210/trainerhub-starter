'use client';

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import { publicApi } from '@/lib/api';

type CatalogEntityType = 'video' | 'program' | 'bundle';
type CatalogItem = {
  id?: string;
  slug?: string;
  title?: string;
  name?: string;
  description?: string;
  short_description?: string;
  trainer_name?: string;
  trainer?: { full_name?: string; display_name?: string; email?: string };
  price?: string | number;
  amount?: string | number;
  currency?: string;
  entityType: CatalogEntityType;
};

function getItemTitle(item: CatalogItem): string {
  return item.title || item.name || 'Без названия';
}

function getItemDescription(item: CatalogItem): string {
  return item.short_description || item.description || 'Описание пока не заполнено.';
}

function getItemTrainer(item: CatalogItem): string {
  return (
    item.trainer_name ||
    item.trainer?.display_name ||
    item.trainer?.full_name ||
    'TrainerHub'
  );
}

function getItemPrice(item: CatalogItem): string {
  const value = item.price ?? item.amount ?? '—';
  const currency = item.currency || 'RUB';
  return `${value} ${currency}`;
}

function getItemHref(item: CatalogItem): string {
  const slug = item.slug || item.id || '';
  if (item.entityType === 'video') return `/catalog/videos/${slug}`;
  if (item.entityType === 'program') return `/catalog/programs/${slug}`;
  return `/catalog/bundles/${slug}`;
}

export default function CatalogPage() {
  const [items, setItems] = useState<CatalogItem[]>([]);
  const [query, setQuery] = useState('');
  const [type, setType] = useState<'all' | CatalogEntityType>('all');
  const [loading, setLoading] = useState(true);
  const [msg, setMsg] = useState('');

  useEffect(() => {
    (async () => {
      try {
        setLoading(true);
        setMsg('');

        const [videos, programs, bundles] = await Promise.all([
          publicApi.listVideos(),
          publicApi.listPrograms(),
          publicApi.listBundles(),
        ]);

        const merged: CatalogItem[] = [
          ...(videos || []).map((item: any) => ({ ...item, entityType: 'video' as const })),
          ...(programs || []).map((item: any) => ({ ...item, entityType: 'program' as const })),
          ...(bundles || []).map((item: any) => ({ ...item, entityType: 'bundle' as const })),
        ];

        setItems(merged);
      } catch (err) {
        setMsg(err instanceof Error ? err.message : 'Не удалось загрузить каталог');
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const filtered = useMemo(() => {
    return items.filter((item) => {
      const matchesType = type === 'all' ? true : item.entityType === type;
      const q = query.trim().toLowerCase();

      const haystack = [
        getItemTitle(item),
        getItemDescription(item),
        getItemTrainer(item),
        item.entityType,
      ]
        .join(' ')
        .toLowerCase();

      const matchesQuery = q ? haystack.includes(q) : true;

      return matchesType && matchesQuery;
    });
  }, [items, query, type]);

  return (
    <section className="stack" style={{ gap: 28 }}>
      <div className="stack" style={{ gap: 10 }}>
        <span className="badge">Каталог</span>
        <h1>Контент для тренировок и фитнеса</h1>
        <p className="lead">
          Найди видео, программы и наборы тренировок. Каталог собирается из
          реальных публичных endpoint’ов backend.
        </p>
      </div>

      <div className="card">
        <div className="grid-2">
          <div className="form-group">
            <label className="label" htmlFor="search">
              Поиск
            </label>
            <input
              id="search"
              className="input"
              placeholder="Например: functional, strength, yoga..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
          </div>

          <div className="form-group">
            <label className="label" htmlFor="type">
              Тип контента
            </label>
            <select
              id="type"
              className="select"
              value={type}
              onChange={(e) => setType(e.target.value as 'all' | CatalogEntityType)}
            >
              <option value="all">Все</option>
              <option value="video">Видео</option>
              <option value="program">Программы</option>
              <option value="bundle">Bundles</option>
            </select>
          </div>
        </div>
      </div>

      {msg ? (
        <div className="card error">{msg}</div>
      ) : loading ? (
        <div className="grid-3">
          {Array.from({ length: 6 }).map((_, idx) => (
            <div className="card content-card" key={idx}>
              <div className="content-card__cover" />
              <div className="content-card__body">
                <span className="badge">Загрузка</span>
                <div className="divider" />
                <p className="muted">Получаем контент из backend API...</p>
              </div>
            </div>
          ))}
        </div>
      ) : filtered.length === 0 ? (
        <div className="empty-state">
          <h3>Ничего не найдено</h3>
          <p>Попробуй изменить поиск или фильтр типа контента.</p>
        </div>
      ) : (
        <div className="grid-3">
          {filtered.map((item) => (
            <article className="card content-card" key={`${item.entityType}-${item.slug || item.id}`}>
              <div className="content-card__cover" />
              <div className="content-card__body">
                <div className="content-card__meta">
                  <span className="badge">
                    {item.entityType === 'video'
                      ? 'Видео'
                      : item.entityType === 'program'
                        ? 'Программа'
                        : 'Bundle'}
                  </span>
                  <span className="price">{getItemPrice(item)}</span>
                </div>

                <div className="stack" style={{ gap: 8 }}>
                  <h3 className="title-md">{getItemTitle(item)}</h3>
                  <p className="muted">Тренер: {getItemTrainer(item)}</p>
                  <p>{getItemDescription(item)}</p>
                </div>

                <div className="row">
                  <span className="muted">Slug: {item.slug || '—'}</span>
                  <Link href={getItemHref(item)} className="button">
                    Открыть
                  </Link>
                </div>
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}