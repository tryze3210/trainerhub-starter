import type { ProductInclude } from './product-detail-utils';

const outcomes: ProductInclude[] = [
  {
    title: 'Понятный маршрут',
    description: 'Ученик видит, с чего начать и что делать дальше.',
  },
  {
    title: 'Контроль прогресса',
    description: 'Пройденные материалы и доступы остаются в системе.',
  },
  {
    title: 'Меньше ручной переписки',
    description: 'Оплата, доступ и обучение собраны в одном сценарии.',
  },
];

export function ProductOutcomeSection() {
  return (
    <section className="premium-product-section" aria-labelledby="product-outcomes-title">
      <div className="premium-product-section-header">
        <span className="premium-eyebrow">Результат сценария</span>
        <h2 id="product-outcomes-title">Какой результат получает ученик</h2>
      </div>
      <div className="premium-product-outcome-grid">
        {outcomes.map((item) => (
          <article className="premium-product-outcome-card" key={item.title}>
            <h3>{item.title}</h3>
            <p>{item.description}</p>
          </article>
        ))}
      </div>
    </section>
  );
}
