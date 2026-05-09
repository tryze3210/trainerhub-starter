import { apiRequest } from '@/lib/api-client';
import type { TrainerApplication, TrainerOnboardingState, TrainerProfileSummary } from '@/modules/trainer-onboarding/api';

export type AdminTrainerApplication = TrainerApplication & {
  user: {
    id: string;
    email: string;
    role: string;
    is_active: boolean;
    is_staff: boolean;
  };
  profile: TrainerProfileSummary | null;
  reviewable: boolean;
  admin_hrefs: {
    detail: string;
    review: string;
    sync_access: string;
  };
};

export type AdminTrainerApplicationListResponse = {
  count: number;
  limit: number;
  results: AdminTrainerApplication[];
};

export type AdminTrainerApplicationReviewResponse = {
  application: AdminTrainerApplication;
  onboarding_state: TrainerOnboardingState;
};

export type ReviewTrainerApplicationPayload = {
  decision: 'approve' | 'reject' | 'request_changes' | 'under_review';
  reviewer_note?: string;
};

export type TrainerApplicationReadinessStatus = 'healthy' | 'warning' | 'degraded' | 'empty' | string;

export type TrainerApplicationReadinessSummary = {
  total_applications: number;
  by_status: Record<string, number>;
  review_queue_count: number;
  approved_count: number;
  dashboard_ready_count: number;
  issue_count: number;
  critical_count: number;
  warning_count: number;
  info_count: number;
  stale_after_days: number;
};

export type TrainerApplicationReadinessCheck = {
  code: string;
  status: string;
  description: string;
};

export type TrainerApplicationReadinessIssue = {
  code: string;
  severity: 'critical' | 'warning' | 'info' | string;
  message: string;
  application_id?: string;
  user_id?: string;
  user_email?: string;
  application_status?: string;
  details?: Record<string, unknown>;
  remediation?: string;
  application?: AdminTrainerApplication;
};

export type TrainerApplicationReadinessResponse = {
  status: TrainerApplicationReadinessStatus;
  generated_at: string;
  summary: TrainerApplicationReadinessSummary;
  checks: TrainerApplicationReadinessCheck[];
  issues: TrainerApplicationReadinessIssue[];
  api_surface: Record<string, string[]>;
  recommendations: string[];
  commands: string[];
};

export type TrainerApplicationReadinessParams = {
  limit?: number;
  stale_after_days?: number;
  include_samples?: boolean;
  include_recommendations?: boolean;
};

function buildQuery(params: Record<string, string | number | boolean | undefined>) {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== '') {
      search.set(key, String(value));
    }
  });
  const query = search.toString();
  return query ? `?${query}` : '';
}

export const adminTrainerApplicationsApi = {
  list: (params: { status?: string; search?: string; limit?: number } = {}) =>
    apiRequest<AdminTrainerApplicationListResponse>(`/trainers/admin/applications/${buildQuery(params)}`, { auth: true }),
  get: (applicationId: string) =>
    apiRequest<AdminTrainerApplication>(`/trainers/admin/applications/${applicationId}/`, { auth: true }),
  review: (applicationId: string, payload: ReviewTrainerApplicationPayload) =>
    apiRequest<AdminTrainerApplicationReviewResponse>(`/trainers/admin/applications/${applicationId}/review/`, {
      auth: true,
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  syncAccess: (applicationId: string) =>
    apiRequest<AdminTrainerApplicationReviewResponse>(`/trainers/admin/applications/${applicationId}/sync-access/`, {
      auth: true,
      method: 'POST',
      body: JSON.stringify({}),
    }),
  getReadiness: (params: TrainerApplicationReadinessParams = {}) =>
    apiRequest<TrainerApplicationReadinessResponse>(`/trainers/admin/applications/readiness/${buildQuery(params)}`, { auth: true }),
};
