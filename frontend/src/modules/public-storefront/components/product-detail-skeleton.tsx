export function ProductDetailSkeleton() {
  return (
    <main className="premium-landing premium-product-page">
      <div className="premium-container">
        <section className="premium-product-skeleton" aria-label="Готовим страницу продукта">
          <div>
            <span />
            <strong />
            <i />
            <i />
          </div>
          <aside>
            <strong />
            <i />
            <i />
            <i />
          </aside>
        </section>
        <section className="premium-product-state">
          <span className="premium-eyebrow">Загрузка</span>
          <h1>Готовим страницу продукта</h1>
          <p>Загружаем описание, цену и данные тренера.</p>
        </section>
      </div>
    </main>
  );
}
