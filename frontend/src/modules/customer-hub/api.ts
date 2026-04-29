import { apiRequest } from '@/lib/api-client';
import type { CustomerMarketplaceHub } from '@/types/api';

export const customerHubApi = {
  getHub: (days = 30) =>
    apiRequest<CustomerMarketplaceHub>(`/customer/hub/?days=${days}`, {
      auth: true,
    }),
};
