'use client';

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import { publicStorefrontApi } from '@/modules/public-storefront/api';
import type { TrainerProfile } from '@/types/api';

function metric(value?: number | string): string {
  if (value === undefined || value === null || value === '') return '0';
  return String(value);
}

function tags(value?: string[]): string[] {
  return Array.isArray(value) ? value.filter(Boolean).slice(0, 4) : [];
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
    <main className="stack page-shell">
      <section className="hero card stack">
        <span className="eyebrow">Public trainers</span>
        <h1>Витрина тренеров</h1>
        <p>
          Страница тренера становится storefront: позиционирование, social proof, specialties,
          активный каталог и CTA на покупку контента.
        </p>
        <div className="actions">
          <Link className="btn btn-primary" href="/catalog">
            Открыть каталог
          </Link>
          <Link className="btn" href="/trainer/onboarding">
            Стать тренером
          </Link>
        </div>
      </section>

      <section className="card stack">
        <div className="section-heading">
          <div>
            <span className="eyebrow">Search</span>
            <h2>Найти тренера</h2>
          </div>
          <span className="badge">{filtered.length} trainers</span>
        </div>
        <input
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Функционалка, йога, реабилитация, имя тренера..."
        />
      </section>

      {error ? <div className="card danger">{error}</div> : null}

      {loading ? (
        <section className="grid-3">
          {Array.from({ length: 6 }).map((_, index) => (
            <article className="card stack" key={index}>
              <span className="badge">Загрузка</span>
              <h3>Получаем профиль тренера...</h3>
              <p>Собираем публичные данные и marketplace metrics.</p>
            </article>
          ))}
        </section>
      ) : filtered.length === 0 ? (
        <section className="card stack">
          <h2>Публичных тренеров пока нет</h2>
          <p>Когда профили будут approved и опубликованы, они появятся в этом каталоге.</p>
        </section>
      ) : (
        <section className="grid-3">
          {filtered.map((trainer) => (
            <article className="card stack" key={trainer.id}>
              <span className="eyebrow">Public storefront</span>
              <div className="section-heading">
                <h3>{trainer.display_name}</h3>
                <span className="badge">{metric(trainer.active_products_count)} products</span>
              </div>
              <p>{trainer.headline || 'Headline пока не заполнен.'}</p>
              <p className="muted">{trainer.bio || 'Описание тренера пока не заполнено.'}</p>
              <div className="actions compact">
                {tags(trainer.specialties).map((tag) => (
                  <span className="badge" key={tag}>{tag}</span>
                ))}
                {tags(trainer.languages).map((lang) => (
                  <span className="badge" key={lang}>{lang}</span>
                ))}
              </div>
              <div className="grid-3 compact">
                <span>Rating {metric(trainer.rating ?? trainer.rating_avg)}</span>
                <span>Reviews {metric(trainer.reviews_count)}</span>
                <span>Students {metric(trainer.students_count)}</span>
              </div>
              <Link className="btn btn-primary" href={`/trainers/${trainer.slug}`}>
                Открыть storefront
              </Link>
            </article>
          ))}
        </section>
      )}
    </main>
  );
}
