'use client';

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';

import {
  buildContentCheckoutHref,
  publicStorefrontApi,
  type StorefrontEntityType,
  type StorefrontItem,
} from '@/modules/public-storefront/api';
import type { PublicBundle, PublicProgram, PublicVideo } from '@/types/api';

import { ProductAccessSection } from './product-access-section';
import { ProductDetailSkeleton } from './product-detail-skeleton';
import { ProductDetailState } from './product-detail-state';
import { ProductIncludesSection } from './product-includes-section';
import { ProductLandingHero } from './product-landing-hero';
import { ProductOutcomeSection } from './product-outcome-section';
import { ProductPurchasePanel } from './product-purchase-panel';
import { ProductTrainerSection } from './product-trainer-section';

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
        if (mounted) setError(err instanceof Error ? err.message : 'Не удалось загрузить описание.');
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
    return <ProductDetailSkeleton />;
  }

  if (error || !item) {
    return (
      <ProductDetailState
        title="Страница продукта недоступна"
        description="Не удалось загрузить описание. Вернитесь в каталог или попробуйте обновить страницу."
      />
    );
  }

  return (
    <main className="premium-landing premium-product-page">
      <div className="premium-container premium-product-layout">
        <div className="premium-product-main">
          <ProductLandingHero item={item} type={type} />
          <ProductIncludesSection type={type} />
          <ProductOutcomeSection />
          <ProductTrainerSection item={item} />
          <ProductAccessSection />
          <section className="premium-product-section premium-product-final">
            <h2>Готовы открыть доступ к продукту?</h2>
            <p>Покупка активирует материалы в личном кабинете и сохраняет обучение в одном рабочем пространстве.</p>
            <div className="premium-actions">
              <Link href={checkoutHref} className="premium-primary-button">
                Купить доступ
              </Link>
              <Link href="/catalog" className="premium-secondary-button">
                Вернуться в каталог
              </Link>
            </div>
          </section>
        </div>

        <ProductPurchasePanel item={item} type={type} />
      </div>
      <ProductPurchasePanel item={item} type={type} mobile />
    </main>
  );
}
