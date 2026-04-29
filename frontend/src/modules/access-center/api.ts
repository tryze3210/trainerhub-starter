import { apiRequest } from '@/lib/api-client';
import type { AccessCenterPayload, AccessDecision } from '@/types/api';

export const accessCenterApi = {
  getAccessCenter: (days = 30) =>
    apiRequest<AccessCenterPayload>(`/entitlements/access-center/?days=${days}`, { auth: true }),

  checkAccess: (payload: { target_type: string; target_id?: string }) =>
    apiRequest<AccessDecision>('/entitlements/check-access/', {
      auth: true,
      method: 'POST',
      body: JSON.stringify(payload),
    }),
};
