import { productAccessSteps } from './product-detail-utils';

export function ProductAccessSection() {
  return (
    <section className="premium-product-section" aria-labelledby="product-access-title">
      <div className="premium-product-section-header">
        <span className="premium-eyebrow">После оплаты</span>
        <h2 id="product-access-title">Что происходит после оплаты</h2>
      </div>
      <div className="premium-access-timeline">
        {productAccessSteps.map((step) => (
          <article className="premium-access-step" key={step.number}>
            <span>{step.number}</span>
            <div>
              <h3>{step.title}</h3>
              <p>{step.description}</p>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
