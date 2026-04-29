import { apiRequest, normalizeListResponse } from '@/lib/api-client';
import type { CheckoutResponse, Order } from '@/types/api';

export const checkoutApi = {
  async listOrders(): Promise<Order[]> {
    const payload = await apiRequest<Order[] | { results: Order[] }>('/orders/', { auth: true });
    return normalizeListResponse(payload);
  },

  checkoutOneTime: (payload: {
    item_type: string;
    item_id: string;
    title?: string;
    amount?: string;
    currency?: string;
    provider?: string;
  }) =>
    apiRequest<CheckoutResponse>('/orders/checkout/', {
      auth: true,
      method: 'POST',
      body: JSON.stringify({
        mode: 'one_time',
        currency: payload.currency || 'RUB',
        provider: payload.provider || 'mock',
        ...payload,
      }),
    }),
};
