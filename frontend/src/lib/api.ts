const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000/api/v1';

async function jsonFetch(path: string, init?: RequestInit) {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers || {}),
    },
    cache: 'no-store',
  });
  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }
  return response.json();
}

export const commerceApi = {
  listOrders: () => jsonFetch('/orders/'),
  checkoutOneTime: (payload: { item_type: string; item_id: string; title: string; amount: string }) =>
    jsonFetch('/orders/checkout/', { method: 'POST', body: JSON.stringify({ mode: 'one_time', ...payload }) }),
  checkoutSubscription: (payload: { plan_id: string }) =>
    jsonFetch('/orders/checkout/', { method: 'POST', body: JSON.stringify({ mode: 'subscription', ...payload }) }),
  listPayments: () => jsonFetch('/payments/'),
  listSubscriptions: () => jsonFetch('/subscriptions/'),
  listEntitlements: () => jsonFetch('/entitlements/'),
  simulateWebhookSuccess: (payload: { external_payment_id: string }) =>
    jsonFetch('/payments-webhooks/receive/', {
      method: 'POST',
      body: JSON.stringify({
        provider: 'mock',
        event_type: 'payment.succeeded',
        external_event_id: `evt-${Date.now()}`,
        payload,
      }),
    }),
};
