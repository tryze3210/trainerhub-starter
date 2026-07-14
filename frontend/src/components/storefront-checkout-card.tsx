'use client';

import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { useAuthSession } from '@/components/auth-provider';
import { privateApi } from '@/lib/api';
import { checkoutApi } from '@/modules/checkout/api';
import { toCheckoutProviderOption, type CheckoutProviderOption } from '@/modules/checkout/components/checkout-payment-method';

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
  const [provider, setProvider] = useState('');
  const [providerOptions, setProviderOptions] = useState<CheckoutProviderOption[]>([]);
  const [loadingProviders, setLoadingProviders] = useState(true);
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState('');

  useEffect(() => {
    let isMounted = true;

    async function loadPaymentSettings() {
      try {
        const payload = await checkoutApi.getPaymentSettings();
        if (!isMounted) return;

        const options = payload.providers
          .map((item) => toCheckoutProviderOption(item.provider, item.display_name))
          .filter((item): item is CheckoutProviderOption => Boolean(item));
        const defaultOption = options.find((item) => item.value === payload.default_provider) || options[0];

        setProviderOptions(options);
        setProvider(defaultOption?.value || '');
        setMsg(options.length ? '' : 'Сейчас нет доступного способа оплаты.');
      } catch (err) {
        if (!isMounted) return;
        setProviderOptions([]);
        setProvider('');
        setMsg(err instanceof Error ? err.message : 'Не удалось загрузить способы оплаты.');
      } finally {
        if (isMounted) {
          setLoadingProviders(false);
        }
      }
    }

    void loadPaymentSettings();

    return () => {
      isMounted = false;
    };
  }, []);

  async function handleCheckout() {
    try {
      if (!provider) {
        setMsg('Выберите доступный способ оплаты.');
        return;
      }

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
            disabled={loadingProviders || !providerOptions.length}
          >
            {providerOptions.map((option) => (
              <option key={option.value} value={option.value}>{option.label}</option>
            ))}
          </select>
        </div>

        {msg ? <div className="card error compact">{msg}</div> : null}
        {isAuthenticated ? (
          <button className="button lg w-full" disabled={loading || loadingProviders || !provider} onClick={() => void handleCheckout()}>
            {loading || loadingProviders ? 'Готовим оплату...' : 'Купить доступ'}
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
