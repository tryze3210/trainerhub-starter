'use client';

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';

import { AnimatedSection } from '@/design-system';
import {
  buildContentCheckoutHref,
  getStorefrontDescription,
  getStorefrontHref,
  getStorefrontPrice,
  publicStorefrontApi,
  type StorefrontEntityType,
  type StorefrontItem,
} from '@/modules/public-storefront/api';

import { PremiumMarketplaceCard } from './premium-marketplace-card';

type CatalogFilter = {
  id: string;
  label: string;
  match: (item: StorefrontItem) => boolean;
};

const filters: CatalogFilter[] = [
  { id: 'all', label: 'Все', match: () => true },
  { id: 'program', label: 'Программы', match: (item) => item.entity_type === 'program' },
  { id: 'video', label: 'Видео', match: (item) => item.entity_type === 'video' },
  { id: 'subscription', label: 'Подписки', match: (item) => `${item.title} ${item.description}`.toLowerCase().includes('подпис') },
  { id: 'bundle', label: 'Наборы', match: (item) => item.entity_type === 'bundle' },
  { id: 'beginner', label: 'Для новичков', match: (item) => `${item.difficulty} ${item.description}`.toLowerCase().includes('нов') },
  { id: 'strength', label: 'Сила', match: (item) => `${item.title} ${item.category} ${item.description}`.toLowerCase().includes('сил') },
  { id: 'mobility', label: 'Мобильность', match: (item) => `${item.title} ${item.category} ${item.description}`.toLowerCase().includes('моб') },
  { id: 'weight', label: 'Похудение', match: (item) => `${item.title} ${item.category} ${item.description}`.toLowerCase().includes('похуд') },
  { id: 'premium', label: 'Премиум', match: (item) => Boolean(item.is_featured) },
];

const fallbackItems: StorefrontItem[] = [
  {
    id: 'demo-strength',
    slug: 'demo-strength',
    title: 'Сила и мобильность',
    short_description: 'Структурная программа для уверенного старта силовых тренировок и восстановления движения.',
    category: 'Сила',
    difficulty: 'Для новичков',
    price_amount: '6900',
    currency: 'RUB',
    duration_minutes: 420,
    trainer_name: 'TrainerHub Studio',
    is_featured: true,
    entity_type: 'program',
  },
  {
    id: 'demo-video',
    slug: 'demo-video',
    title: 'Техника базовых упражнений',
    short_description: 'Видеоуроки с короткими объяснениями, которые помогают тренироваться без лишней путаницы.',
    category: 'Видео',
    difficulty: 'любой уровень',
    price_amount: '1900',
    currency: 'RUB',
    duration_minutes: 95,
    trainer_name: 'TrainerHub Academy',
    entity_type: 'video',
  },
  {
    id: 'demo-bundle',
    slug: 'demo-bundle',
    title: 'Премиум-набор для запуска формы',
    short_description: 'Программа, видео и материалы в одном доступе для системного старта.',
    category: 'Премиум',
    difficulty: 'средний уровень',
    price_amount: '9900',
    currency: 'RUB',
    duration_minutes: 560,
    trainer_name: 'TrainerHub Pro',
    is_featured: true,
    entity_type: 'bundle',
  },
];

function useCatalogItems() {
  const [items, setItems] = useState<StorefrontItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let mounted = true;

    async function load() {
      try {
        setLoading(true);
        setError('');
        const catalog = await publicStorefrontApi.listCatalog();
        if (mounted) setItems(catalog.length > 0 ? catalog : fallbackItems);
      } catch (err) {
        if (mounted) {
          setError(err instanceof Error ? err.message : 'Не удалось загрузить каталог. Попробуйте обновить страницу.');
          setItems(fallbackItems);
        }
      } finally {
        if (mounted) setLoading(false);
      }
    }

    void load();
    return () => {
      mounted = false;
    };
  }, []);

  return { items, loading, error };
}

function PremiumCatalogFilters({
  activeFilter,
  onFilterChange,
}: {
  activeFilter: string;
  onFilterChange: (filterId: string) => void;
}) {
  return (
    <div className="premium-filter-bar premium-catalog-filter-row" aria-label="Фильтры каталога">
      {filters.map((filter) => (
        <button
          className={`premium-filter-chip premium-catalog-filter-button ${activeFilter === filter.id ? 'premium-filter-chip-active' : ''}`}
          key={filter.id}
          onClick={() => onFilterChange(filter.id)}
          type="button"
        >
          {filter.label}
        </button>
      ))}
    </div>
  );
}

function PremiumFeaturedProduct({ item }: { item: StorefrontItem }) {
  return (
    <section className="premium-featured-product premium-catalog-featured" aria-labelledby="featured-product-title">
      <div className="premium-featured-product-grid">
        <div>
          <span className="premium-eyebrow">Рекомендуем начать с этого</span>
          <h2 id="featured-product-title">{item.title}</h2>
          <p>{getStorefrontDescription(item)}</p>
          <div className="premium-marketplace-card-chips">
            <span>{item.entity_type === 'program' ? 'программа' : item.entity_type === 'video' ? 'видео' : 'набор'}</span>
            <span>{item.difficulty || 'любой уровень'}</span>
            <span>{item.duration_minutes ? `${item.duration_minutes} мин` : 'материалы внутри'}</span>
          </div>
        </div>
        <aside>
          <span>{item.trainer_name || 'TrainerHub'}</span>
          <strong>{getStorefrontPrice(item)}</strong>
          <div className="premium-marketplace-card-actions">
            <Link href={getStorefrontHref(item)} className="premium-secondary-button">
              Подробнее
            </Link>
            <Link href={buildContentCheckoutHref(item)} className="premium-primary-button">
              Купить
            </Link>
          </div>
        </aside>
      </div>
    </section>
  );
}

function PremiumCatalogState({ title, description }: { title: string; description?: string }) {
  return (
    <div className="premium-state-card premium-catalog-state">
      <strong>{title}</strong>
      {description ? <p>{description}</p> : null}
    </div>
  );
}

function PremiumSkeletonGrid() {
  return (
    <div className="premium-product-grid premium-catalog-skeleton-grid">
      {Array.from({ length: 6 }).map((_, index) => (
        <div className="premium-skeleton-card" key={index}>
          <span />
          <strong />
          <i />
          <i />
        </div>
      ))}
    </div>
  );
}

export function MarketplaceCatalogPage() {
  const { items, loading, error } = useCatalogItems();
  const [activeFilter, setActiveFilter] = useState('all');

  const filtered = useMemo(() => {
    const filter = filters.find((item) => item.id === activeFilter) ?? filters[0];
    return items.filter(filter.match);
  }, [activeFilter, items]);

  const featured = items.find((item) => item.is_featured) ?? items[0] ?? fallbackItems[0];

  return (
    <main className="premium-landing premium-catalog-page">
      <section className="premium-catalog-hero" aria-labelledby="catalog-title">
        <div className="premium-container premium-catalog-hero-grid">
          <div className="premium-catalog-hero-content">
            <span className="premium-eyebrow">MARKETPLACE</span>
            <h1 className="premium-hero-title" id="catalog-title">
              Каталог программ и тренеров
            </h1>
            <p className="premium-hero-subtitle">
              Выбирайте программы, видеоуроки и подписки от тренеров. Покупайте доступ, продолжайте обучение в личном
              кабинете и отслеживайте прогресс.
            </p>
          </div>
          <aside className="premium-catalog-preview premium-catalog-proof-row" aria-label="Как работает доступ после покупки">
            {['Доступ после оплаты', 'Прогресс уроков', 'Материалы и задания', 'Связь с тренером'].map((item) => (
              <span key={item}>{item}</span>
            ))}
          </aside>
        </div>
      </section>

      <div className="premium-container">
        <AnimatedSection className="premium-section">
          <PremiumFeaturedProduct item={featured} />
        </AnimatedSection>

        <AnimatedSection className="premium-section premium-catalog-shell premium-catalog-products" aria-labelledby="catalog-products-title">
          <div className="premium-section-header premium-catalog-toolbar">
            <span className="premium-eyebrow">PROGRAMS / VIDEO / ACCESS</span>
            <h2 className="premium-section-title" id="catalog-products-title">
              Выберите формат под цель обучения
            </h2>
          </div>

          <PremiumCatalogFilters activeFilter={activeFilter} onFilterChange={setActiveFilter} />

          {error ? (
            <PremiumCatalogState title="Не удалось загрузить каталог. Попробуйте обновить страницу." description={error} />
          ) : null}

          {loading ? (
            <PremiumSkeletonGrid />
          ) : filtered.length === 0 ? (
            <PremiumCatalogState title="Пока нет программ по выбранному фильтру" />
          ) : (
            <div className="premium-product-grid premium-catalog-grid">
              {filtered.map((item) => (
                <PremiumMarketplaceCard item={item} key={`${item.entity_type}:${item.id}`} />
              ))}
            </div>
          )}
        </AnimatedSection>

        <AnimatedSection className="premium-section">
          <div className="premium-trainer-spotlight premium-catalog-spotlight">
            <span className="premium-eyebrow">TRAINER SPOTLIGHT</span>
            <h2>Тренер остаётся в центре продукта</h2>
            <p>
              Каталог показывает не только программу, но и контекст: кто ведёт обучение, что входит в доступ и как ученик
              продолжит работу после покупки.
            </p>
            <Link href="/trainers" className="premium-secondary-button">
              Смотреть тренеров
            </Link>
          </div>
        </AnimatedSection>

        <AnimatedSection className="premium-section" aria-labelledby="access-title">
          <div className="premium-trust-panel">
            <div className="premium-section-header">
              <span className="premium-eyebrow">ACCESS FLOW</span>
              <h2 className="premium-section-title" id="access-title">
                Как работает доступ
              </h2>
            </div>
            <div className="premium-row-list premium-catalog-flow">
              {[
                'Вы покупаете программу или подписку',
                'TrainerHub активирует доступ в личном кабинете',
                'Материалы, уроки и задания остаются в одном месте',
                'Тренер видит прогресс и может сопровождать обучение',
              ].map((step, index) => (
                <div className="premium-row-list__item" key={step}>
                  <span>{String(index + 1).padStart(2, '0')}</span>
                  <p>{step}</p>
                </div>
              ))}
            </div>
          </div>
        </AnimatedSection>

        <AnimatedSection className="premium-section premium-final-cta-section">
          <div className="premium-final-cta premium-catalog-final-cta">
            <span className="premium-eyebrow">TRAINERHUB MARKETPLACE</span>
            <h2>Готовы выбрать программу и продолжить обучение в одном кабинете?</h2>
            <p>Откройте каталог, сравните формат, уровень и тренера, затем получите доступ без ручной переписки.</p>
            <div className="premium-actions">
              <Link href="/catalog" className="premium-primary-button">
                Смотреть каталог
              </Link>
              <Link href="/register" className="premium-secondary-button">
                Создать аккаунт
              </Link>
            </div>
          </div>
        </AnimatedSection>
      </div>
    </main>
  );
}
