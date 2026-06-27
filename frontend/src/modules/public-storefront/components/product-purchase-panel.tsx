import Link from 'next/link';

import {
  buildContentCheckoutHref,
  type StorefrontEntityType,
  type StorefrontItem,
} from '@/modules/public-storefront/api';

import {
  getProductDuration,
  getProductLevel,
  getProductPrice,
  getProductTrainer,
  PRODUCT_TYPE_LABELS,
} from './product-detail-utils';

const trustHints = [
  'Доступ активируется после оплаты',
  'Материалы появятся в личном кабинете',
  'Покупка привязана к вашему аккаунту',
];

export function ProductPurchasePanel({
  item,
  type,
  mobile = false,
}: {
  item: StorefrontItem;
  type: StorefrontEntityType;
  mobile?: boolean;
}) {
  const price = getProductPrice(item);

  return (
    <aside className={mobile ? 'premium-mobile-purchase-bar' : 'premium-purchase-panel premium-purchase-panel-sticky'}>
      <div className="premium-purchase-price">
        <span>{PRODUCT_TYPE_LABELS[type]}</span>
        <strong>{price}</strong>
      </div>

      {!mobile ? (
        <>
          <div className="premium-purchase-meta">
            <span>Тренер</span>
            <strong>{getProductTrainer(item)}</strong>
            <span>Уровень</span>
            <strong>{getProductLevel(item)}</strong>
            <span>Длительность</span>
            <strong>{getProductDuration(item)}</strong>
          </div>
          <div className="premium-purchase-trust">
            {trustHints.map((hint) => (
              <span key={hint}>{hint}</span>
            ))}
          </div>
        </>
      ) : null}

      <div className="premium-marketplace-card-actions">
        <Link href={buildContentCheckoutHref(item)} className="premium-primary-button">
          Купить доступ за {price}
        </Link>
        {!mobile ? (
          <Link href="/catalog" className="premium-secondary-button">
            Вернуться в каталог
          </Link>
        ) : null}
      </div>
    </aside>
  );
}
