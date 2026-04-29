import { apiRequest } from '@/lib/api-client';
import type { OnboardingStatus } from '@/types/api';

export const onboardingApi = {
  status: () => apiRequest<OnboardingStatus>('/onboarding/status/', { auth: true }),
  steps: () => apiRequest('/onboarding/steps/', { auth: true }),
  completeStep: (stepCode: string, payload?: Record<string, unknown>) =>
    apiRequest('/onboarding/complete-step/', {
      auth: true,
      method: 'POST',
      body: JSON.stringify({
        step_code: stepCode,
        payload: payload || {},
      }),
    }),
};
