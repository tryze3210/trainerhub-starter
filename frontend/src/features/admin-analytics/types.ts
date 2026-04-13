export type KPIOverview = {
  range_days: number;
  revenue: string;
  gross_revenue: string;
  paid_orders: number;
  total_orders: number;
  new_customers: number;
  new_trainers: number;
  new_subscriptions: number;
  active_subscriptions: number;
  conversion_rate: string;
  arppu: string;
  last_aggregated_date: string | null;
};

export type RevenueSeriesPoint = {
  date: string;
  gross_revenue: string;
  paid_revenue: string;
  total_orders: number;
  paid_orders: number;
};

export type TopTrainer = {
  trainer_id: string;
  paid_revenue: string;
  gross_revenue: string;
  paid_orders: number;
  total_orders: number;
  new_customers: number;
  active_subscribers: number;
};

export type FunnelPoint = {
  date: string;
  signups: number;
  ordering_customers: number;
  paid_customers: number;
  new_subscribers: number;
  signup_to_order_rate: string;
  order_to_paid_rate: string;
  paid_to_subscription_rate: string;
};

export type CohortRetention = {
  cohort_date: string;
  cohort_size: number;
  retained_day_0: number;
  retained_day_1: number;
  retained_day_7: number;
  retained_day_30: number;
  retention_day_1_rate: string;
  retention_day_7_rate: string;
  retention_day_30_rate: string;
};

export type WarehouseHealth = {
  status: string;
  last_success_started_at: string | null;
  last_success_finished_at: string | null;
  last_success_range_start: string | null;
  last_success_range_end: string | null;
  last_success_rows_written: number;
  latest_failure_message: string;
};

export type TrafficPoint = {
  date: string;
  sessions: number;
  unique_users: number;
  page_views: number;
  video_views: number;
  checkout_starts: number;
  purchases: number;
};

export type TopPath = {
  path: string;
  sessions: number;
  page_views: number;
  video_views: number;
  checkout_starts: number;
  purchases: number;
};

export type AttributionRow = {
  utm_source: string;
  utm_medium: string;
  utm_campaign: string;
  sessions: number;
  page_views: number;
  purchases: number;
};

export type TrafficFilters = {
  source?: string;
  medium?: string;
  campaign?: string;
  trainer_id?: string;
  path_prefix?: string;
};
