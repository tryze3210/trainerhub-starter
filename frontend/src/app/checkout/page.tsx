import { Suspense } from 'react';
import { CheckoutPage } from '@/modules/checkout/components/checkout-page';

export default function CheckoutRoute() {
  return (
    <Suspense fallback={<div className="premium-checkout-state">Готовим оформление доступа...</div>}>
      <CheckoutPage />
    </Suspense>
  );
}
