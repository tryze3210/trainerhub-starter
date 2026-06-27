'use client';

import { useMemo, useRef, useState } from 'react';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuthSession } from '@/components/auth-provider';
import { checkoutApi } from '@/modules/checkout/api';
import { CheckoutOrderSummary, formatCheckoutPrice } from '@/modules/checkout/components/checkout-order-summary';
import { CheckoutPaymentMethod, type CheckoutProvider } from '@/modules/checkout/components/checkout-payment-method';
import { CheckoutStateCard } from '@/modules/checkout/components/checkout-state-card';
import { CheckoutTrustPanel } from '@/modules/checkout/components/checkout-trust-panel';

function createIdempotencyKey() {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) {
    return crypto.randomUUID();
  }

  return `checkout-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function redirectUrlFromPayload(payload: Awaited<ReturnType<typeof checkoutApi.checkoutOneTime>>) {
  const providerPayload = payload.payment.provider_payload || {};
  const providerRedirect =
    typeof providerPayload.redirect_url === 'string'
      ? providerPayload.redirect_url
      : typeof providerPayload.confirmation_url === 'string'
        ? providerPayload.confirmation_url
        : '';

  return payload.payment.checkout_url || payload.payment.external_checkout_url || providerRedirect;
}

export function CheckoutPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { isAuthenticated, isLoading } = useAuthSession();
  const [provider, setProvider] = useState<CheckoutProvider>('mock');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState<{ orderId?: string; paymentId?: string } | null>(null);
  const idempotencyKey = useRef(createIdempotencyKey());

  const checkoutParams = useMemo(
    () => ({
      item_type: searchParams.get('item_type') || '',
      item_id: searchParams.get('item_id') || '',
      title: searchParams.get('title') || 'Выбранный продукт',
      amount: searchParams.get('amount') || '0',
      currency: searchParams.get('currency') || 'RUB',
    }),
    [searchParams]
  );

  const loginHref = useMemo(() => {
    const query = searchParams.toString();
    return `/login?next=${encodeURIComponent(`/checkout${query ? `?${query}` : ''}`)}`;
  }, [searchParams]);

  async function submitCheckout() {
    if (!checkoutParams.item_type || !checkoutParams.item_id) {
      setError('Не удалось определить продукт для покупки. Вернитесь в каталог и выберите продукт заново.');
      return;
    }

    setError('');
    setIsSubmitting(true);

    try {
      const payload = await checkoutApi.checkoutOneTime({
        ...checkoutParams,
        provider,
        idempotency_key: idempotencyKey.current,
      });
      const redirectUrl = redirectUrlFromPayload(payload);

      if (redirectUrl) {
        window.location.assign(redirectUrl);
        return;
      }

      const orderId = payload.order.id;
      const paymentId = payload.payment.id;
      setResult({ orderId, paymentId });
      router.replace(`/checkout/success?order_id=${encodeURIComponent(orderId)}&payment_id=${encodeURIComponent(paymentId)}${provider === 'mock' ? '&mock=1' : ''}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось создать заказ. Попробуйте ещё раз.');
      setIsSubmitting(false);
    }
  }

  if (isLoading) {
    return (
      <div className="premium-checkout-page">
        <CheckoutStateCard title="Готовим оформление доступа" description="Проверяем сессию и параметры покупки." />
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <div className="premium-checkout-page">
        <CheckoutStateCard
          title="Чтобы оформить доступ, войдите в аккаунт"
          description="После входа вы вернётесь к этой покупке и сможете подтвердить заказ."
          primaryHref={loginHref}
          primaryLabel="Войти и продолжить"
          secondaryHref="/catalog"
          secondaryLabel="Вернуться в каталог"
        />
      </div>
    );
  }

  return (
    <div className="premium-checkout-page">
      <section className="premium-checkout-hero">
        <span className="premium-eyebrow">Покупка доступа</span>
        <h1>Оформление доступа</h1>
        <p>Проверьте продукт, стоимость и подтвердите покупку. После успешной оплаты доступ появится в личном кабинете.</p>
      </section>

      <div className="premium-checkout-layout">
        <div className="premium-checkout-panel">
          <CheckoutOrderSummary
            title={checkoutParams.title}
            itemType={checkoutParams.item_type}
            amount={checkoutParams.amount}
            currency={checkoutParams.currency}
          />
          <CheckoutTrustPanel />
        </div>

        <aside className="premium-checkout-panel premium-checkout-panel-sticky">
          <div className="premium-checkout-total">
            <span>Итого</span>
            <strong>{formatCheckoutPrice(checkoutParams.amount, checkoutParams.currency)}</strong>
          </div>

          <CheckoutPaymentMethod provider={provider} onProviderChange={setProvider} />

          {error ? <div className="premium-checkout-error">{error}</div> : null}
          {result ? (
            <div className="premium-checkout-success">
              Заказ создан. Если переход не произошёл автоматически, откройте подтверждение оплаты вручную.
            </div>
          ) : null}

          <button className="premium-primary-button" type="button" disabled={isSubmitting} onClick={() => void submitCheckout()}>
            {isSubmitting ? 'Создаём заказ...' : 'Подтвердить покупку'}
          </button>

          <Link href="/catalog" className="premium-secondary-button">Вернуться в каталог</Link>
        </aside>
      </div>
    </div>
  );
}
