import { apiRequest, normalizeListResponse } from '@/lib/api-client';
import type { Entitlement, Order, Payment, Subscription } from '@/types/api';

export type CustomerBillingSnapshot = {
  orders: Order[];
  payments: Payment[];
  subscriptions: Subscription[];
  entitlements: Entitlement[];
};

async function list<T>(path: string): Promise<T[]> {
  const payload = await apiRequest<T[] | { results: T[] }>(path, { auth: true });
  return normalizeListResponse(payload);
}

export const customerBillingApi = {
  async getSnapshot(): Promise<CustomerBillingSnapshot> {
    const [orders, payments, subscriptions, entitlements] = await Promise.all([
      list<Order>('/orders/'),
      list<Payment>('/payments/'),
      list<Subscription>('/subscriptions/'),
      list<Entitlement>('/entitlements/'),
    ]);

    return {
      orders,
      payments,
      subscriptions,
      entitlements,
    };
  },
};
