import Link from 'next/link';

import type { StorefrontItem } from '@/modules/public-storefront/api';

import { getProductTrainer } from './product-detail-utils';

export function ProductTrainerSection({ item }: { item: StorefrontItem }) {
  const trainer = getProductTrainer(item);

  return (
    <section className="premium-product-section" aria-labelledby="product-trainer-title">
      <article className="premium-product-trainer-card">
        <div>
          <span className="premium-eyebrow">Автор продукта</span>
          <h2 id="product-trainer-title">{trainer}</h2>
          <p>
            Продукт опубликован тренером в TrainerHub. После покупки доступ появляется в кабинете ученика, а тренер
            сохраняет контекст продукта, продаж и сопровождения.
          </p>
        </div>
        {item.trainer_slug ? (
          <Link href={`/trainers/${item.trainer_slug}`} className="premium-secondary-button">
            Смотреть страницу тренера
          </Link>
        ) : null}
      </article>
    </section>
  );
}
