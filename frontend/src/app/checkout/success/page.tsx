'use client';

import { Suspense } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { useEffect, useState } from 'react';
import { privateApi } from '@/lib/api';

function CheckoutSuccessPageContent() {
  const searchParams = useSearchParams();
  const paymentId = searchParams.get('payment_id') || '';
  const orderId = searchParams.get('order_id') || '';
  const isMock = searchParams.get('mock') === '1';
  const [msg, setMsg] = useState('');

  useEffect(() => {
    if (!paymentId || !isMock) return;
    void (async () => {
      try {
        await privateApi.confirmMockPayment(paymentId);
      } catch (err) {
        setMsg(err instanceof Error ? err.message : 'Не удалось подтвердить платёж');
      }
    })();
  }, [isMock, paymentId]);

  return (
    <section className="stack" style={{ gap: 24 }}>
      <div className="card dark">
        <span className="badge success">Checkout success</span>
        <h1 className="title-lg">Оплата завершена</h1>
        <p className="lead">Заказ и платёж уже можно открыть в личном кабинете.</p>
      </div>
      {msg ? <div className="card error">{msg}</div> : null}
      <div className="inline">
        {orderId ? <Link href={`/orders/${orderId}`} className="button">Открыть заказ</Link> : null}
        {paymentId ? <Link href={`/payments/${paymentId}`} className="button secondary">Открыть платёж</Link> : null}
        <Link href="/entitlements" className="button ghost">Мои доступы</Link>
      </div>
    </section>
  );
}

export default function CheckoutSuccessPage() {
  return (
    <Suspense fallback={<div>Загрузка...</div>}>
      <CheckoutSuccessPageContent />
    </Suspense>
  );
}

