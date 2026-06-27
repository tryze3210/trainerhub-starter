import Link from 'next/link';

import {
  buildContentCheckoutHref,
  getStorefrontDescription,
  getStorefrontHref,
  getStorefrontPrice,
  type StorefrontEntityType,
  type StorefrontItem,
} from '@/modules/public-storefront/api';

const TYPE_LABELS: Record<StorefrontEntityType, string> = {
  video: 'Видео',
  program: 'Программа',
  bundle: 'Набор',
};

function metric(value: number | string | undefined, fallback: string): string {
  if (value === undefined || value === null || value === '') return fallback;
  return String(value);
}

export function PremiumMarketplaceCard({ item }: { item: StorefrontItem }) {
  const duration = item.duration_minutes ? `${item.duration_minutes} мин` : 'Материалы внутри';

  return (
    <article className="premium-marketplace-card">
      <div className="premium-marketplace-card-cover">
        <span>{TYPE_LABELS[item.entity_type]}</span>
      </div>
      <div className="premium-marketplace-card-body">
        <div className="premium-marketplace-card-meta">
          <span>{item.trainer_name || 'TrainerHub'}</span>
          <span>{metric(item.difficulty, 'любой уровень')}</span>
        </div>
        <h3>{item.title}</h3>
        <p>{getStorefrontDescription(item)}</p>
        <div className="premium-marketplace-card-chips">
          <span>{item.category || 'тренировки'}</span>
          <span>{duration}</span>
          <span>{item.is_featured ? 'премиум' : 'доступ после оплаты'}</span>
        </div>
        <div className="premium-marketplace-card-price">
          <small>Стоимость доступа</small>
          <strong>{getStorefrontPrice(item)}</strong>
        </div>
        <div className="premium-marketplace-card-actions">
          <Link href={getStorefrontHref(item)} className="premium-secondary-button">
            Подробнее
          </Link>
          <Link href={buildContentCheckoutHref(item)} className="premium-primary-button">
            Купить
          </Link>
        </div>
      </div>
    </article>
  );
}
