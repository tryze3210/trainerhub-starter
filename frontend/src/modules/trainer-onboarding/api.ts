import { apiRequest } from '@/lib/api-client';
import type { OnboardingStatus } from '@/types/api';

export type TrainerApplicationStatus =
  | 'draft'
  | 'submitted'
  | 'under_review'
  | 'approved'
  | 'changes_requested'
  | 'rejected';

export type TrainerApplicationPayload = {
  legal_name?: string;
  brand_name?: string;
  contact_phone?: string;
  country?: string;
  city?: string;
  specialties?: string[];
  links?: string[];
  bio?: string;
  experience_years?: number;
};

export type TrainerApplication = TrainerApplicationPayload & {
  id?: string;
  status: TrainerApplicationStatus;
  submitted_at?: string | null;
  reviewed_at?: string | null;
  reviewer_note?: string;
  latest_moderation_case_id?: string | null;
  moderation_snapshot?: Record<string, unknown>;
  required_fields?: Record<string, boolean>;
  is_complete?: boolean;
  created_at?: string;
  updated_at?: string;
};

export type TrainerProfileSummary = {
  id: string;
  slug: string;
  display_name: string;
  headline: string;
  bio: string;
  status: string;
  is_public: boolean;
};

export type TrainerOnboardingStep = {
  code: string;
  title: string;
  description: string;
  is_completed: boolean;
  is_blocked: boolean;
  action_href?: string | null;
};

export type TrainerOnboardingState = {
  user?: {
    id: string;
    email: string;
    role: string;
    is_staff: boolean;
  };
  application: TrainerApplication;
  profile: TrainerProfileSummary | null;
  dashboard_unlocked: boolean;
  can_submit_application: boolean;
  can_edit_application: boolean;
  can_access_content_studio: boolean;
  summary: {
    total_steps: number;
    completed_steps: number;
    completion_percent: number;
    next_step: string;
    next_step_title: string;
    status: string;
  };
  steps: TrainerOnboardingStep[];
};

export const trainerOnboardingApi = {
  getStatus: () => apiRequest<TrainerOnboardingState>('/trainers/me/onboarding/status/', { auth: true }),
  getApplicationStatus: () => apiRequest<TrainerOnboardingState>('/trainers/me/application-status/', { auth: true }),
  getApplication: () => apiRequest<TrainerApplication>('/trainers/me/application/', { auth: true }),
  saveApplication: (payload: TrainerApplicationPayload) =>
    apiRequest<TrainerApplication>('/trainers/me/application/', {
      auth: true,
      method: 'PATCH',
      body: JSON.stringify(payload),
    }),
  submitApplication: (payload: TrainerApplicationPayload) =>
    apiRequest<TrainerApplication>('/trainers/me/application/submit/', {
      auth: true,
      method: 'POST',
      body: JSON.stringify(payload),
    }),
};

// Backward-compatible alias for legacy trainer dashboard imports.
// Keep this pointed at the original onboarding API shape so existing pages that
// expect OnboardingStatus do not receive the richer TrainerOnboardingState shape.
export const onboardingApi = {
  status: () => apiRequest<OnboardingStatus>('/onboarding/status/', { auth: true }),
  steps: () => apiRequest<unknown>('/onboarding/steps/', { auth: true }),
  completeStep: (stepCode: string, payload?: Record<string, unknown>) =>
    apiRequest<OnboardingStatus>('/onboarding/complete-step/', {
      auth: true,
      method: 'POST',
      body: JSON.stringify({ step_code: stepCode, payload: payload || {} }),
    }),
};
