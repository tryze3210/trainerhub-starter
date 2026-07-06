'use client';

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import { AnimatedSection } from '@/design-system';
import { publicStorefrontApi } from '@/modules/public-storefront/api';
import type { TrainerProfile } from '@/types/api';

function metric(value?: number | string): string {
  if (value === undefined || value === null || value === '') return '0';
  return String(value);
}

function tags(value?: string[]): string[] {
  return Array.isArray(value) ? value.filter(Boolean).slice(0, 4) : [];
}

function initials(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  return parts
    .slice(0, 2)
    .map((part) => part[0])
    .join('')
    .toUpperCase() || 'TH';
}

export function TrainerDirectoryPage() {
  const [trainers, setTrainers] = useState<TrainerProfile[]>([]);
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let mounted = true;

    async function load() {
      try {
        setLoading(true);
        setError('');
        const payload = await publicStorefrontApi.listTrainers();
        if (mounted) setTrainers(payload);
      } catch (err) {
        if (mounted) setError(err instanceof Error ? err.message : 'Ошибка загрузки тренеров');
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
    return trainers.filter((trainer) => {
      const haystack = [
        trainer.display_name,
        trainer.headline,
        trainer.bio,
        ...(trainer.specialties || []),
        ...(trainer.languages || []),
      ]
        .filter(Boolean)
        .join(' ')
        .toLowerCase();
      return normalized ? haystack.includes(normalized) : true;
    });
  }, [query, trainers]);

  return (
    <div className="premium-landing premium-trainers-page">
      <section className="premium-trainers-hero" aria-labelledby="trainers-title">
        <div className="premium-container premium-trainers-hero-grid">
          <div className="premium-trainers-hero-content">
            <span className="premium-eyebrow">TRAINER MARKETPLACE</span>
            <h1 className="premium-hero-title" id="trainers-title">
              Витрина тренеров
            </h1>
            <p className="premium-hero-subtitle">
              Выбирайте тренера по специализации, языку, продуктам и социальному доказательству. Открывайте storefront,
              сравнивайте программы и покупайте доступ в едином сценарии TrainerHub.
            </p>
            <div className="premium-actions premium-trainers-actions">
              <Link className="premium-primary-button" href="/catalog">
                Открыть каталог
              </Link>
              <Link className="premium-secondary-button" href="/trainer/onboarding">
                Стать тренером
              </Link>
            </div>
          </div>

          <aside className="premium-trainers-proof" aria-label="Ключевые показатели витрины тренеров">
            <div>
              <strong>{metric(trainers.length)}</strong>
              <span>тренеров в витрине</span>
            </div>
            <div>
              <strong>{metric(trainers.reduce((sum, trainer) => sum + (trainer.active_products_count || 0), 0))}</strong>
              <span>активных продуктов</span>
            </div>
            <div>
              <strong>{metric(trainers.reduce((sum, trainer) => sum + (trainer.reviews_count || 0), 0))}</strong>
              <span>отзывов учеников</span>
            </div>
          </aside>
        </div>
      </section>

      <div className="premium-container">
        <AnimatedSection className="premium-section premium-trainers-directory" aria-labelledby="trainers-search-title">
          <div className="premium-section-header premium-trainers-toolbar">
            <div>
              <span className="premium-eyebrow">SEARCH / SPECIALTIES / STORE</span>
              <h2 className="premium-section-title" id="trainers-search-title">
                Найти тренера под цель
              </h2>
            </div>
            <span className="premium-trainers-count">{filtered.length} trainers</span>
          </div>

          <label className="premium-trainers-search">
            <span>Поиск по имени, специализации или языку</span>
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Функционалка, йога, реабилитация, имя тренера..."
            />
          </label>

          {error ? (
            <div className="premium-state-card premium-trainers-state">
              <strong>Не удалось загрузить тренеров</strong>
              <p>{error}</p>
            </div>
          ) : null}

          {loading ? (
            <div className="premium-trainers-grid">
              {Array.from({ length: 6 }).map((_, index) => (
                <article className="premium-trainer-card premium-trainer-card-loading" key={index}>
                  <span />
                  <strong />
                  <i />
                  <i />
                </article>
              ))}
            </div>
          ) : filtered.length === 0 ? (
            <div className="premium-state-card premium-trainers-state">
              <strong>Публичных тренеров пока нет</strong>
              <p>Когда профили будут approved и опубликованы, они появятся в этой витрине.</p>
            </div>
          ) : (
            <div className="premium-trainers-grid">
              {filtered.map((trainer) => (
                <article className="premium-trainer-card" key={trainer.id}>
                  <div className="premium-trainer-card-cover">
                    {trainer.avatar_url ? (
                      <img src={trainer.avatar_url} alt="" />
                    ) : (
                      <span>{initials(trainer.display_name)}</span>
                    )}
                    <small>{metric(trainer.active_products_count)} products</small>
                  </div>

                  <div className="premium-trainer-card-body">
                    <div className="premium-trainer-card-meta">
                      <span>Public storefront</span>
                      <span>Rating {metric(trainer.rating ?? trainer.rating_avg)}</span>
                    </div>
                    <h3>{trainer.display_name}</h3>
                    <p className="premium-trainer-card-headline">{trainer.headline || 'Позиционирование тренера пока не заполнено.'}</p>
                    <p className="premium-trainer-card-description">{trainer.bio || 'Описание тренера пока не заполнено.'}</p>

                    <div className="premium-trainer-card-chips">
                      {[...tags(trainer.specialties), ...tags(trainer.languages)].slice(0, 6).map((tag) => (
                        <span key={tag}>{tag}</span>
                      ))}
                    </div>

                    <div className="premium-trainer-card-stats">
                      <span>
                        <strong>{metric(trainer.reviews_count)}</strong>
                        Reviews
                      </span>
                      <span>
                        <strong>{metric(trainer.students_count)}</strong>
                        Students
                      </span>
                      <span>
                        <strong>{metric(trainer.views_count)}</strong>
                        Views
                      </span>
                    </div>

                    <Link className="premium-primary-button" href={`/trainers/${trainer.slug}`}>
                      Открыть storefront
                    </Link>
                  </div>
                </article>
              ))}
            </div>
          )}
        </AnimatedSection>
      </div>
    </div>
  );
}
