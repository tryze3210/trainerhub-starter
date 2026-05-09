import { apiRequest } from '@/lib/api-client';

export type TrainerPayoutWallet = {
  exists: boolean;
  id: string | null;
  currency: string;
  available_amount: string;
  pending_amount: string;
  locked_amount: string;
  reserved_amount: string;
  lifetime_earned_amount: string;
  minimum_payout_amount: string;
  can_request_payout: boolean;
};

export type TrainerPayoutRequest = {
  id: string;
  created_at: string | null;
  updated_at: string | null;
  requested_at: string | null;
  approved_at: string | null;
  processed_at: string | null;
  amount: string;
  currency: string;
  status: string;
  destination_masked: string;
  rejected_reason: string;
  trainer?: {
    id: string;
    user_id: string;
    slug: string;
    display_name: string;
  };
  wallet_id: string;
  metadata: Record<string, unknown>;
};

export type TrainerPayoutListResponse = {
  count: number;
  limit: number;
  results: TrainerPayoutRequest[];
};

export type TrainerPayoutCreateResponse = {
  payout: TrainerPayoutRequest;
  wallet: TrainerPayoutWallet;
};

export function getTrainerPayoutBalance() {
  return apiRequest<TrainerPayoutWallet>('/payouts/my/balance/', { auth: true });
}

export function listTrainerPayoutRequests(limit = 50, status?: string) {
  const search = new URLSearchParams({ limit: String(limit) });
  if (status) search.set('status', status);
  return apiRequest<TrainerPayoutListResponse>(`/payouts/my/?${search.toString()}`, { auth: true });
}

export function createTrainerPayoutRequest(payload: { amount: string; destination_masked: string }) {
  return apiRequest<TrainerPayoutCreateResponse>('/payouts/my/request/', {
    auth: true,
    method: 'POST',
    body: JSON.stringify(payload),
  });
}
