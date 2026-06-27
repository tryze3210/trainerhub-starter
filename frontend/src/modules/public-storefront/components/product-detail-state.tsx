import Link from 'next/link';

export function ProductDetailState({ title, description }: { title: string; description: string }) {
  return (
    <main className="premium-landing premium-product-page">
      <div className="premium-container">
        <section className="premium-product-state">
          <span className="premium-eyebrow">Страница продукта</span>
          <h1>{title}</h1>
          <p>{description}</p>
          <Link href="/catalog" className="premium-secondary-button">
            Вернуться в каталог
          </Link>
        </section>
      </div>
    </main>
  );
}
