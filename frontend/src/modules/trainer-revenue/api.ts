import { apiRequest } from '@/lib/api-client';

export type TrainerRevenueSummary = {
  period: {
    days: number;
    since: string;
    until: string;
  };
  trainer: {
    id: string;
    slug: string;
    display_name: string;
    status: string;
  };
  currency: string;
  wallet: {
    currency: string;
    available_amount: string;
    pending_amount: string;
    reserved_amount: string;
    locked_amount: string;
    lifetime_earned: string;
  };
  revenue: {
    gross_sales: string;
    platform_commission: string;
    net_revenue: string;
    refunds: string;
    chargebacks: string;
    paid_out: string;
    pending_payout: string;
    available_payout: string;
    reserved_balance: string;
  };
  counts: {
    transactions: number;
    payout_requests: number;
    paid_payouts: number;
  };
  top_sources: Array<{
    source_type: string;
    source_id: string | null;
    net_revenue: string;
    transaction_count: number;
  }>;
  notes: string[];
};

export type TrainerRevenueTransaction = {
  id: string;
  created_at: string | null;
  entry_type: string;
  direction: string;
  amount: string;
  currency: string;
  status: string;
  source_type: string;
  source_id: string | null;
  description: string;
};

export type TrainerRevenuePayout = {
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
  destination_json?: Record<string, unknown>;
  metadata: Record<string, unknown>;
};

export type TrainerRevenueListResponse<T> = {
  trainer: {
    id: string;
    slug: string;
    display_name: string;
  };
  currency?: string;
  limit: number;
  count: number;
  results: T[];
};

export function getTrainerRevenueSummary(days = 30) {
  return apiRequest<TrainerRevenueSummary>(`/trainers/me/revenue/summary/?days=${days}`, { auth: true });
}

export function getTrainerRevenueTransactions(limit = 50) {
  return apiRequest<TrainerRevenueListResponse<TrainerRevenueTransaction>>(
    `/trainers/me/revenue/transactions/?limit=${limit}`,
    { auth: true }
  );
}

export function getTrainerRevenuePayouts(limit = 50) {
  return apiRequest<TrainerRevenueListResponse<TrainerRevenuePayout>>(
    `/trainers/me/revenue/payouts/?limit=${limit}`,
    { auth: true }
  );
}
