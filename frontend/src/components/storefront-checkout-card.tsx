'use client';

import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { useState } from 'react';
import { useAuthSession } from '@/components/auth-provider';
import { privateApi } from '@/lib/api';

const providerOptions = [
  { value: 'mock', label: 'Тестовая оплата' },
  { value: 'cloudpayments', label: 'CloudPayments' },
  { value: 'yookassa', label: 'ЮKassa' },
];

export function StorefrontCheckoutCard({
  itemType,
  itemId,
  title,
  amount,
  currency,
}: {
  itemType: string;
  itemId: string;
  title: string;
  amount?: string;
  currency?: string;
}) {
  const pathname = usePathname();
  const router = useRouter();
  const { isAuthenticated } = useAuthSession();
  const [provider, setProvider] = useState('mock');
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState('');

  async function handleCheckout() {
    try {
      setLoading(true);
      setMsg('');
      const payload = await privateApi.checkoutOneTime({
        item_type: itemType,
        item_id: itemId,
        title,
        amount,
        currency,
        provider,
      });
      const paymentId = payload.payment.id;
      if (provider === 'mock') {
        router.push(`/checkout/success?payment_id=${paymentId}&order_id=${payload.order.id}&mock=1`);
        return;
      }
      router.push(`/payments/${paymentId}?provider_redirect=1`);
    } catch (err) {
      setMsg(err instanceof Error ? err.message : 'Не удалось создать заказ');
    } finally {
      setLoading(false);
    }
  }

  return (
    <aside className="card sticky-card">
      <div className="stack" style={{ gap: 14 }}>
        <span className="badge">Покупка</span>
        <h3 className="title-md">Купить доступ</h3>
        <p className="muted">{amount || '—'} {currency || 'RUB'}</p>

        <div className="form-group">
          <label className="label" htmlFor={`provider-${itemType}-${itemId}`}>Платёжный провайдер</label>
          <select
            id={`provider-${itemType}-${itemId}`}
            className="select"
            value={provider}
            onChange={(event) => setProvider(event.target.value)}
          >
            {providerOptions.map((option) => (
              <option key={option.value} value={option.value}>{option.label}</option>
            ))}
          </select>
        </div>

        {msg ? <div className="card error compact">{msg}</div> : null}
        {isAuthenticated ? (
          <button className="button lg w-full" disabled={loading} onClick={() => void handleCheckout()}>
            {loading ? 'Создаём заказ...' : 'Купить доступ'}
          </button>
        ) : (
          <Link className="button lg w-full" href={`/login?next=${encodeURIComponent(pathname || '/')}`}>
            Войти и купить
          </Link>
        )}
        <p className="muted">
          После подтверждения оплаты доступ появится в личном кабинете. Для внешних провайдеров будет создана платёжная сессия.
        </p>
      </div>
    </aside>
  );
}
