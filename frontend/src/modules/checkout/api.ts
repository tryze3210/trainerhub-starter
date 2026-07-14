import { apiRequest, normalizeListResponse } from '@/lib/api-client';

import type { CheckoutResponse, Order, PublicCheckoutPaymentSettings } from '@/types/api';

type CheckoutOneTimePayload = {
  item_type: string;
  item_id: string;
  title?: string;
  amount?: string;
  currency?: string;
  provider: string;
  idempotency_key?: string;
};

export const checkoutApi = {
  async listOrders(): Promise<Order[]> {
    const payload = await apiRequest<Order[] | { results: Order[] }>('/orders/', { auth: true });
    return normalizeListResponse<Order>(payload);
  },

  checkoutOneTime: (payload: CheckoutOneTimePayload): Promise<CheckoutResponse> => {
    const headers = payload.idempotency_key
      ? { 'Idempotency-Key': payload.idempotency_key }
      : undefined;

    return apiRequest<CheckoutResponse>('/orders/checkout/', {
      auth: true,
      method: 'POST',
      headers,
      body: JSON.stringify({
        mode: 'one_time',
        currency: payload.currency || 'RUB',
        ...payload,
      }),
    });
  },

  getPaymentSettings: (): Promise<PublicCheckoutPaymentSettings> => {
    return apiRequest<PublicCheckoutPaymentSettings>('/platform-settings/checkout-payment-providers/');
  },
};
