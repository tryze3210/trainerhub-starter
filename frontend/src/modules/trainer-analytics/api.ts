import { apiRequest } from '@/lib/api-client';

export type TrainerAnalyticsMoney = string;

export type TrainerAnalyticsPeriod = {
  days: number;
  since: string;
  until: string;
};

export type TrainerAnalyticsTrainer = {
  id: string;
  slug: string;
  display_name: string;
  status: string;
};

export type TrainerContentPerformanceRow = {
  content_type: 'video' | 'product';
  id: string;
  slug: string;
  title: string;
  status: string;
  product_type?: string;
  access_type?: string;
  is_free: boolean;
  price_amount: TrainerAnalyticsMoney | null;
  currency: string;
  views_count: number;
  purchase_count: number;
  conversion_rate: string;
  gross_revenue: TrainerAnalyticsMoney;
  refund_amount: TrainerAnalyticsMoney;
  net_revenue: TrainerAnalyticsMoney;
  product_count: number;
  created_at: string | null;
  updated_at: string | null;
};

export type TrainerAnalyticsOverview = {
  period: TrainerAnalyticsPeriod;
  trainer: TrainerAnalyticsTrainer;
  currency: string;
  counts: {
    videos: number;
    products: number;
    published_videos: number;
    published_products: number;
    free_videos: number;
    paid_products: number;
  };
  sales: {
    matched_sales: number;
    purchased_units: number;
    gross_order_sales: TrainerAnalyticsMoney;
  };
  performance: {
    gross_revenue: TrainerAnalyticsMoney;
    refund_amount: TrainerAnalyticsMoney;
    net_revenue: TrainerAnalyticsMoney;
    total_views: number;
    total_purchases: number;
  };
  top_content: TrainerContentPerformanceRow[];
  notes: string[];
};

export type TrainerContentAnalyticsResponse = {
  period: TrainerAnalyticsPeriod;
  trainer: TrainerAnalyticsTrainer;
  currency: string;
  content_type: 'all' | 'video' | 'product';
  limit: number;
  count: number;
  summary: TrainerAnalyticsOverview['performance'];
  results: TrainerContentPerformanceRow[];
};

export type TrainerSaleAnalyticsRow = {
  order_id: string;
  created_at: string | null;
  item_type: string;
  item_id: string;
  title: string;
  quantity: number;
  unit_price: TrainerAnalyticsMoney;
  total_price: TrainerAnalyticsMoney;
  currency: string;
  order_status: string;
  matched_content_type: 'video' | 'product';
  matched_content_id: string;
};

export type TrainerSalesAnalyticsResponse = {
  period: TrainerAnalyticsPeriod;
  trainer: TrainerAnalyticsTrainer;
  currency: string;
  limit: number;
  count: number;
  summary: TrainerAnalyticsOverview['sales'];
  results: TrainerSaleAnalyticsRow[];
};

export function getTrainerAnalyticsOverview(days = 30) {
  return apiRequest<TrainerAnalyticsOverview>(`/trainers/me/analytics/overview/?days=${days}`, { auth: true });
}

export function getTrainerContentAnalytics(type: 'all' | 'video' | 'product' = 'all', days = 30, limit = 50) {
  return apiRequest<TrainerContentAnalyticsResponse>(
    `/trainers/me/analytics/content/?type=${type}&days=${days}&limit=${limit}`,
    { auth: true }
  );
}

export function getTrainerSalesAnalytics(days = 30, limit = 50) {
  return apiRequest<TrainerSalesAnalyticsResponse>(`/trainers/me/analytics/sales/?days=${days}&limit=${limit}`, {
    auth: true,
  });
}
