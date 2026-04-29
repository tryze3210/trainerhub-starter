import { apiRequest, normalizeListResponse } from '@/lib/api-client';
import type { Entitlement, Payment, Subscription } from '@/types/api';

export const paymentsApi = {
  async listPayments(): Promise<Payment[]> {
    const payload = await apiRequest<Payment[] | { results: Payment[] }>('/payments/', { auth: true });
    return normalizeListResponse(payload);
  },

  async listSubscriptions(): Promise<Subscription[]> {
    const payload = await apiRequest<Subscription[] | { results: Subscription[] }>('/subscriptions/', {
      auth: true,
    });
    return normalizeListResponse(payload);
  },

  async listEntitlements(): Promise<Entitlement[]> {
    const payload = await apiRequest<Entitlement[] | { results: Entitlement[] }>('/entitlements/', {
      auth: true,
    });
    return normalizeListResponse(payload);
  },

  simulatePaymentSuccess: (externalPaymentId: string) =>
    apiRequest<{ webhook_event_id: string; processed_at: string }>('/payments-webhooks/receive/', {
      method: 'POST',
      body: JSON.stringify({
        provider: 'mock',
        event_type: 'payment.succeeded',
        external_event_id: `evt-${Date.now()}`,
        payload: {
          external_payment_id: externalPaymentId,
        },
      }),
    }),
};
