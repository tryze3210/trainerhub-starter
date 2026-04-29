'use client';

import { Suspense } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';

function CheckoutCancelPageContent() {
  const searchParams = useSearchParams();
  const paymentId = searchParams.get('payment_id') || '';
  const orderId = searchParams.get('order_id') || '';

  return (
    <section className="stack" style={{ gap: 24 }}>
      <div className="card dark">
        <span className="badge warning">Checkout cancelled</span>
        <h1 className="title-lg">Оплата не завершена</h1>
        <p className="lead">Платёж был отменён или завершился ошибкой. Можно вернуться к заказу и попробовать снова.</p>
      </div>
      <div className="inline">
        {orderId ? <Link href={`/orders/${orderId}`} className="button">Открыть заказ</Link> : null}
        {paymentId ? <Link href={`/payments/${paymentId}`} className="button secondary">Открыть платёж</Link> : null}
        <Link href="/catalog" className="button ghost">Вернуться в каталог</Link>
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

