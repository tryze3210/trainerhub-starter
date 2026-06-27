import type { StorefrontEntityType } from '@/modules/public-storefront/api';

import { buildProductIncludes } from './product-detail-utils';

export function ProductIncludesSection({ type }: { type: StorefrontEntityType }) {
  const includes = buildProductIncludes(type);

  return (
    <section className="premium-product-section" aria-labelledby="product-includes-title">
      <div className="premium-product-section-header">
        <span className="premium-eyebrow">Доступ</span>
        <h2 id="product-includes-title">Что входит в доступ</h2>
      </div>
      <div className="premium-product-includes-grid">
        {includes.map((item) => (
          <article className="premium-product-include-card" key={item.title}>
            <h3>{item.title}</h3>
            <p>{item.description}</p>
          </article>
        ))}
      </div>
    </section>
  );
}
