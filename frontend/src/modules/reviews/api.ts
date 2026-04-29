import { apiRequest, normalizeListResponse } from '@/lib/api-client';

export type Review = {
  id: string;
  target_type: string;
  target_id: string;
  target_title?: string;
  target_slug?: string;
  trainer_id?: string;
  author_name: string;
  rating: number;
  title: string;
  body: string;
  status: string;
  verified_purchase?: boolean;
  quality_flags?: string[];
  moderation_note?: string;
  moderated_by_id?: string;
  moderated_at?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
};

export type ReviewSummary = {
  target_type: string;
  target_id: string;
  reviews_count: number;
  average_rating: number;
};

export type ReviewEligibility = {
  can_review: boolean;
  code: string;
  reason: string;
  entitlement_id?: string | null;
  verified_purchase?: boolean;
  target?: Record<string, unknown>;
};

export type ReviewPayload = {
  summary: ReviewSummary;
  items: Review[];
  viewer_review?: Review | null;
  eligibility?: ReviewEligibility;
};

export type ReviewTrustCenter = {
  period_days: number;
  total_reviews: number;
  period_reviews: number;
  pending_count: number;
  published_count: number;
  rejected_count: number;
  flagged_count: number;
  verified_purchase_count: number;
  average_rating: number;
  low_rating_count: number;
  status_counts: Record<string, number>;
  period_status_counts: Record<string, number>;
  recent_low_rating: Review[];
};

export type TrainerReviewQuality = {
  period_days: number;
  summary: {
    total_reviews: number;
    period_reviews: number;
    published_count: number;
    pending_count: number;
    rejected_count: number;
    flagged_count: number;
    average_rating: number;
    low_rating_count: number;
  };
  by_target: Array<{
    target_type: string;
    target_id: string;
    target_title: string;
    target_slug?: string;
    reviews_count: number;
    average_rating: number;
  }>;
  recent_reviews: Review[];
  readiness: Array<{ code: string; label: string; is_ok: boolean; severity: string }>;
};

export const reviewsApi = {
  getTargetReviews: (targetType: string, targetId: string): Promise<ReviewPayload> =>
    apiRequest<ReviewPayload>(`/reviews/${targetType}/${targetId}/`),

  createReview: (targetType: string, targetId: string, payload: { rating: number; title: string; body: string }): Promise<Review> =>
    apiRequest<Review>(`/reviews/${targetType}/${targetId}/`, {
      auth: true,
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  listAdminReviews: (status = 'pending'): Promise<Review[]> =>
    apiRequest<Review[] | { results: Review[] }>(`/reviews/admin/pending/?status=${encodeURIComponent(status)}`, { auth: true }).then(normalizeListResponse),

  getAdminTrustCenter: (days = 30): Promise<ReviewTrustCenter> =>
    apiRequest<ReviewTrustCenter>(`/reviews/admin/trust-center/?days=${days}`, { auth: true }),

  moderateReview: (reviewId: string, decision: 'publish' | 'reject' | 'flag', note = ''): Promise<Review> =>
    apiRequest<Review>(`/reviews/admin/${reviewId}/moderate/`, {
      auth: true,
      method: 'POST',
      body: JSON.stringify({ decision, note }),
    }),

  getTrainerQuality: (days = 30): Promise<TrainerReviewQuality> =>
    apiRequest<TrainerReviewQuality>(`/reviews/trainer/quality/?days=${days}`, { auth: true }),
};
