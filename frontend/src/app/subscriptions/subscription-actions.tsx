'use client';

import { createSubscriptionCheckout, cancelSubscription } from '@/lib/api';

export function SubscribeButton({ planId }: { planId: number }) {
  return (
    <button
      onClick={async () => {
        const current = window.location.origin;
        const result = await createSubscriptionCheckout(planId, `${current}/payments/status?result=success`, `${current}/subscriptions?result=cancelled`);
        window.location.href = result.checkout_url;
      }}
    >
      Checkout subscription
    </button>
  );
}

export function CancelSubscriptionButton({ subscriptionId }: { subscriptionId: number }) {
  return <button onClick={() => cancelSubscription(subscriptionId)}>Cancel subscription</button>;
}
