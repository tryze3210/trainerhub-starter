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
    <section className="premium-checkout-page">
      <div className="premium-checkout-state premium-checkout-success">
        <span className="premium-eyebrow">Покупка оформлена</span>
        <h1>Доступ оформлен</h1>
        <p>Оплата завершена. Материалы появятся в личном кабинете после подтверждения платежа.</p>
      </div>
      {msg ? (
        <div className="premium-checkout-error">
          Платёж создан, но автоматическое подтверждение не завершилось. Откройте платёж или обновите статус в кабинете.
        </div>
      ) : null}
      <div className="premium-checkout-actions">
        <Link href="/entitlements" className="premium-primary-button">Перейти к моим доступам</Link>
        {orderId ? <Link href={`/orders/${orderId}`} className="premium-secondary-button">Открыть заказ</Link> : null}
        {paymentId ? <Link href={`/payments/${paymentId}`} className="premium-secondary-button">Открыть платёж</Link> : null}
        <Link href="/catalog" className="premium-secondary-button">Вернуться в каталог</Link>
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
