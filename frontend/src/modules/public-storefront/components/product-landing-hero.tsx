import type { StorefrontEntityType, StorefrontItem } from '@/modules/public-storefront/api';

import {
  buildProductFacts,
  getProductDescription,
  getProductTrainer,
  PRODUCT_TYPE_CONTEXT,
  PRODUCT_TYPE_LABELS,
} from './product-detail-utils';

export function ProductLandingHero({ item, type }: { item: StorefrontItem; type: StorefrontEntityType }) {
  const facts = buildProductFacts(item).slice(0, 4);

  return (
    <section className="premium-product-hero" aria-labelledby="product-title">
      <div className="premium-product-hero-copy">
        <span className="premium-eyebrow">{PRODUCT_TYPE_CONTEXT[type]}</span>
        <h1 className="premium-product-title" id="product-title">
          {item.title}
        </h1>
        <p className="premium-product-subtitle">{getProductDescription(item)}</p>
        <div className="premium-product-meta" aria-label="Краткая информация о продукте">
          <span>{PRODUCT_TYPE_LABELS[type]}</span>
          <span>{getProductTrainer(item)}</span>
          <span>Доступ после оплаты</span>
        </div>
      </div>

      <div className="premium-product-facts">
        {facts.map((fact) => (
          <article className="premium-product-fact" key={fact.label}>
            <span>{fact.label}</span>
            <strong>{fact.value}</strong>
          </article>
        ))}
      </div>
    </section>
  );
}
