'use client';

import { Suspense } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';

function CheckoutCancelPageContent() {
  const searchParams = useSearchParams();
  const paymentId = searchParams.get('payment_id') || '';
  const orderId = searchParams.get('order_id') || '';

  return (
    <section className="premium-checkout-page">
      <div className="premium-checkout-state">
        <span className="premium-eyebrow">Оплата не подтверждена</span>
        <h1>Покупка не завершена</h1>
        <p>Платёж был отменён или не прошёл. Вы можете вернуться к заказу, попробовать снова или выбрать другой продукт в каталоге.</p>
      </div>
      <div className="premium-checkout-actions">
        <Link href="/catalog" className="premium-primary-button">Вернуться в каталог</Link>
        {orderId ? <Link href={`/orders/${orderId}`} className="premium-secondary-button">Открыть заказ</Link> : null}
        {paymentId ? <Link href={`/payments/${paymentId}`} className="premium-secondary-button">Открыть платёж</Link> : null}
      </div>
    </section>
  );
}

export default function CheckoutCancelPage() {
  return (
    <Suspense fallback={<div>Загрузка...</div>}>
      <CheckoutCancelPageContent />
    </Suspense>
  );
}
