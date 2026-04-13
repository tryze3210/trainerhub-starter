import { apiClient } from '@/shared/api/client';

export const moderationApi = {
  getOverview: async () => (await apiClient.get('/api/v1/moderation/admin/overview/')).data,
  getQueue: async () => (await apiClient.get('/api/v1/moderation/admin/queue/')).data,
  submitDecision: async (caseId: string, payload: any) => (await apiClient.post(`/api/v1/moderation/admin/cases/${caseId}/decision/`, payload)).data,
  getRiskFlags: async () => (await apiClient.get('/api/v1/moderation/admin/risk-flags/')).data,
  createRiskFlag: async (payload: any) => (await apiClient.post('/api/v1/moderation/admin/risk-flags/create/', payload)).data,
  getMyStatus: async () => (await apiClient.get('/api/v1/moderation/me/status/')).data,
};
