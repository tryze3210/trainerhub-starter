export type AuthUser = {
  id: string;
  email: string;
  full_name: string;
  display_name?: string;
  phone?: string;
  country?: string;
  city?: string;
  timezone?: string;
  preferred_language?: string;
  active_role: string;
  available_roles: string[];
  is_staff?: boolean;
  is_superuser?: boolean;
  settings?: {
    marketing_emails_enabled?: boolean;
    product_updates_enabled?: boolean;
    push_notifications_enabled?: boolean;
    favorite_categories?: string[];
  };
};

export type SessionPayload = {
  is_authenticated: boolean;
  user: AuthUser | null;
};

export type AuthResponse = {
  user: AuthUser;
  access_token?: string;
  refresh_token?: string;
};

export type PublicVideo = {
  id: string;
  slug: string;
  title: string;
  description: string;
  category?: string;
  difficulty?: string;
  visibility?: string;
  price_amount?: string;
  currency?: string;
  duration_minutes?: number;
  trainer_slug?: string;
  trainer_name?: string;
  is_featured?: boolean;
  is_active?: boolean;
};

export type PublicLesson = {
  id: string;
  slug?: string;
  title: string;
  description?: string;
  position?: number;
  is_preview?: boolean;
  duration_minutes?: number;
};

export type PublicProgram = {
  id: string;
  slug: string;
  title: string;
  description: string;
  category?: string;
  difficulty?: string;
  visibility?: string;
  price_amount?: string;
  currency?: string;
  duration_minutes?: number;
  trainer_slug?: string;
  trainer_name?: string;
  is_featured?: boolean;
  is_active?: boolean;
  lessons?: PublicLesson[];
};

export type PublicBundleItem = {
  id: string;
  item_type: string;
  target_slug?: string;
  target_title?: string;
  position?: number;
};

export type PublicBundle = {
  id: string;
  slug: string;
  title: string;
  description: string;
  category?: string;
  difficulty?: string;
  visibility?: string;
  price_amount?: string;
  currency?: string;
  duration_minutes?: number;
  trainer_slug?: string;
  trainer_name?: string;
  is_featured?: boolean;
  is_active?: boolean;
  items?: PublicBundleItem[];
};

export type TrainerCatalogItem = {
  id: string;
  entity_type: string;
  slug: string;
  title: string;
  trainer_slug: string;
  trainer_name: string;
  category?: string;
  difficulty?: string;
  price?: string;
  currency?: string;
  rating?: number;
  reviews_count?: number;
  duration_minutes?: number;
  is_featured?: boolean;
  cover_url?: string;
  description?: string;
  published_at?: string;
};

export type TrainerProfile = {
  id: string;
  slug: string;
  display_name: string;
  headline?: string;
  bio?: string;
  avatar_url?: string;
  specialties?: string[];
  languages?: string[];
  rating?: number;
  rating_avg?: string | number;
  reviews_count?: number;
  views_count?: number;
  sales_count?: number;
  students_count?: number;
  active_products_count?: number;
  featured_items?: string[];
  status?: string;
  is_public?: boolean;
  catalog_items?: TrainerCatalogItem[];
};

export type Review = {
  id: string;
  target_type: string;
  target_id: string;
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
  trainer_reply?: string;
  trainer_reply_by_id?: string;
  trainer_replied_at?: string | null;
  created_at: string;
  updated_at?: string | null;
};

export type ReviewSummary = {
  target_type: string;
  target_id: string;
  reviews_count: number;
  average_rating: number;
  rating_distribution?: Record<string, number>;
};

export type ReviewPayload = {
  summary: ReviewSummary;
  items: Review[];
  viewer_review?: Review | null;
};

export type OrderItem = {
  id: string;
  item_type?: string;
  item_id?: string;
  title_snapshot?: string;
  quantity?: number;
  unit_price?: string;
  total_price?: string;
  metadata?: Record<string, unknown>;
};

export type Order = {
  id: string;
  order_type?: string;
  status?: string;
  currency?: string;
  total_amount?: string;
  gross_amount?: string;
  amount?: string;
  external_checkout_id?: string;
  paid_at?: string | null;
  completed_at?: string | null;
  created_at?: string | null;
  createdAt?: string | null;
  updated_at?: string | null;
  trainer_name?: string;
  title?: string;
  items?: OrderItem[];
};

export type Payment = {
  id: string;
  order_id?: string;
  provider?: string;
  status?: string;
  amount?: string;
  gross_amount?: string;
  platform_fee_amount?: string;
  trainer_amount?: string;
  currency?: string;
  external_payment_id?: string;
  provider_payment_id?: string;
  external_checkout_url?: string;
  checkout_session_id?: string;
  order_type?: string;
  order_reference?: string;
  provider_payload?: Record<string, unknown>;
  confirmed_at?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
};

export type CheckoutResponse = {
  order: Order;
  payment: {
    id: string;
    provider?: string;
    status?: string;
    checkout_url?: string;
    external_checkout_url?: string;
    provider_payload?: Record<string, unknown>;
  };
};

export type PublicCheckoutPaymentProvider = {
  provider: string;
  display_name?: string;
  environment?: string;
  public_key?: string;
};

export type PublicCheckoutPaymentSettings = {
  default_provider?: string;
  providers: PublicCheckoutPaymentProvider[];
};

export type PayoutBalance = {
  trainer_id: string;
  currency?: string;
  available_amount?: string;
  reserved_amount?: string;
  lifetime_earned_amount?: string;
  updated_at?: string | null;
};

export type PayoutLedgerEntry = {
  id: string;
  payout_request?: string | null;
  payment_id?: string;
  entry_type?: string;
  amount?: string;
  currency?: string;
  metadata?: Record<string, unknown>;
  created_at?: string | null;
  updated_at?: string | null;
};

export type PayoutRequest = {
  id: string;
  trainer_id?: string;
  amount?: string;
  currency?: string;
  status?: string;
  destination_masked?: string;
  requested_at?: string | null;
  approved_at?: string | null;
  processed_at?: string | null;
  rejected_reason?: string;
  metadata?: Record<string, unknown>;
  created_at?: string | null;
  updated_at?: string | null;
  ledger_entries?: PayoutLedgerEntry[];
};

export type SubscriptionPlan = {
  id: string;
  code?: string;
  title?: string;
  period_days?: number;
  price?: string;
  currency?: string;
  is_active?: boolean;
};

export type Subscription = {
  id: string;
  status?: string;
  starts_at?: string | null;
  ends_at?: string | null;
  cancelled_at?: string | null;
  auto_renew?: boolean;
  plan?: SubscriptionPlan;
  plan_name?: string;
  title?: string;
  product_title?: string;
  trainer_name?: string;
  currency?: string;
  amount?: string | number;
  price_amount?: string | number;
  started_at?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
  current_period_start?: string | null;
  current_period_end?: string | null;
  cancel_at?: string | null;
  canceled_at?: string | null;
  is_active?: boolean;
};

export type Entitlement = {
  id: string;
  kind?: string;
  object_id?: string;
  source?: string;
  source_reference?: string | null;
  is_active?: boolean;
  source_type?: string;
  source_order_id?: string | null;
  source_subscription_id?: string | null;
  target_type?: string;
  target_id?: string;
  status?: string;
  starts_at?: string | null;
  ends_at?: string | null;
  metadata?: Record<string, unknown>;
  access_status?: string;
  access_kind?: string;
  entitlement_type?: string;
  content_type?: string;
  content_title?: string;
  title?: string;
  product_title?: string;
  trainer_name?: string;
  granted_at?: string | null;
  expires_at?: string | null;
  revoked_at?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
};

export type OnboardingStep = {
  code: string;
  title: string;
  description: string;
  role_scope: string;
  is_completed: boolean;
  sort_order: number;
};

export type OnboardingStatus = {
  trainer_application_status?: TrainerApplicationStatus | null;
  steps: OnboardingStep[];
  summary: {
    completed_steps: number;
    total_steps: number;
    completion_percent: number;
    next_step: string | null;
  };
};

export type UploadIntentResponse = {
  media_asset_id: string;
  object_key: string;
  upload_url: string;
  upload_method: 'PUT';
  required_headers: Record<string, string>;
  expires_in: number;
};

export type MediaAsset = {
  id: string;
  bucket_name?: string;
  object_key?: string;
  asset_type?: string;
  visibility?: string;
  status?: string;
  content_type?: string;
  file_size_bytes?: number;
  original_filename?: string;
  checksum_sha256?: string;
  metadata_json?: Record<string, unknown>;
};

export type VideoDraft = {
  video_asset_id: string | null;
  current_version_number: number | null;
  price_amount: string;
  currency: string;
  id: string;
  slug: string;
  title: string;
  description?: string;
  duration_seconds?: number;
  is_free: boolean;
  status?: string;
  media_asset?: MediaAsset;
  media_asset_id?: string;
};

export type TrainerCmsDashboard = {
  draft_videos_count?: number;
  published_videos_count?: number;
  draft_programs_count?: number;
  published_programs_count?: number;
  draft_bundles_count?: number;
  published_bundles_count?: number;
  pending_review_count?: number;
  total_sales_count?: number;
};

export type ApiErrorShape = {
  detail?: string;
  [key: string]: unknown;
};


export type PaymentProviderConfig = {
  provider: string;
  display_name?: string;
  is_enabled: boolean;
  environment?: string;
  public_key?: string;
  shop_id?: string;
  webhook_secret_masked?: string;
  return_url_override?: string;
  notes?: string;
};

export type PaymentProviderSettings = {
  default_provider: string;
  providers: PaymentProviderConfig[];
};

export type TrainerRevenueSummary = {
  currency: string;
  available_amount: string;
  reserved_amount: string;
  lifetime_earned_amount: string;
  revenue_last_30_days: string;
  payouts_last_30_days: string;
  paid_orders_count: number;
  payout_requests_count: number;
  pending_payout_requests_count: number;
  avg_order_value: string;
};

export type TrainerRevenueSeriesPoint = {
  date: string;
  accrual_amount: string;
  payout_amount: string;
  orders_count: number;
};

export type TrainerTopProduct = {
  item_type: string;
  title: string;
  revenue: string;
  orders_count: number;
};

export type TrainerRevenueDashboard = {
  summary: TrainerRevenueSummary;
  revenue_series: TrainerRevenueSeriesPoint[];
  top_products: TrainerTopProduct[];
};


export type PayoutStatusBucket = {
  status: string;
  count: number;
  amount: string;
};

export type PayoutLedgerBucket = {
  entry_type: string;
  count: number;
  amount: string;
};

export type PayoutBalanceTotals = {
  available_amount: string;
  reserved_amount: string;
  lifetime_earned_amount: string;
  trainers_count: number;
};

export type PayoutOpsSummary = {
  pending_exposure_amount: string;
  pending_exposure_count: number;
  reserved_amount: string;
  available_amount: string;
};

export type AdminPayoutOverview = {
  statuses: PayoutStatusBucket[];
  ledger: PayoutLedgerBucket[];
  balances: PayoutBalanceTotals;
  ops: PayoutOpsSummary;
  recent_requests: PayoutRequest[];
};

export type ModerationCase = {
  id: string;
  target_type: string;
  target_id: string;
  title: string;
  summary?: string;
  status: string;
  priority: number;
  queue: string;
  latest_decision?: string;
  trainer?: string | null;
  assigned_to?: string | null;
  opened_at?: string | null;
  updated_at?: string | null;
  resolved_at?: string | null;
  events?: ModerationCaseEvent[];
  decisions?: ModerationDecision[];
};

export type ModerationCaseEvent = {
  id: string;
  actor?: string | null;
  event_type: string;
  payload?: Record<string, unknown>;
  created_at?: string | null;
};

export type ModerationDecision = {
  id: string;
  case: string;
  reviewer?: string | null;
  decision: string;
  reason?: string;
  metadata?: Record<string, unknown>;
  created_at?: string | null;
};

export type TrainerRiskFlag = {
  id: string;
  trainer: string;
  code: string;
  label: string;
  risk_level: 'low' | 'medium' | 'high' | 'critical' | string;
  is_active: boolean;
  source?: string;
  details?: Record<string, unknown>;
  created_at?: string | null;
  resolved_at?: string | null;
};

export type ModerationOverview = {
  totals: {
    total: number;
    open: number;
    in_review: number;
    escalated: number;
    resolved: number;
  };
  queues: Array<{ queue: string; total: number; open: number }>;
  risk_levels: Array<{ risk_level: string; count: number }>;
  active_risk_flags: number;
  latest_cases: ModerationCase[];
};

export type AnalyticsKpiOverview = {
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
  last_aggregated_date?: string | null;
};

export type AnalyticsRevenuePoint = {
  date: string;
  gross_revenue: string;
  paid_revenue: string;
  total_orders: number;
  paid_orders: number;
};

export type AnalyticsTopTrainer = {
  trainer_id: string;
  paid_revenue: string;
  gross_revenue: string;
  paid_orders: number;
  total_orders: number;
  new_customers: number;
  active_subscribers: number;
};

export type AnalyticsWarehouseHealth = {
  status: string;
  last_success_started_at?: string | null;
  last_success_finished_at?: string | null;
  last_success_range_start?: string | null;
  last_success_range_end?: string | null;
  last_success_rows_written: number;
  latest_failure_message?: string;
};

export type AdminMarketplaceAlert = {
  severity: 'healthy' | 'warning' | 'critical' | string;
  code: string;
  message: string;
  section: string;
};

export type AdminMarketplaceSummary = {
  revenue: string;
  paid_orders: number;
  open_moderation_cases: number;
  active_risk_flags: number;
  under_review_applications: number;
  approved_trainers: number;
  pending_payout_amount: string;
  pending_payout_count: number;
  payout_reconciliation_issues: number;
  failed_payments: number;
  pending_reviews: number;
};

export type AuditEvent = {
  id: string;
  actor_id?: string | null;
  actor_email?: string;
  event_type: string;
  entity_type: string;
  entity_id: string;
  context?: Record<string, unknown>;
  ip_address?: string | null;
  created_at?: string | null;
};

export type AdminMarketplaceHealth = {
  generated_at: string;
  range_days: number;
  overall_status: 'healthy' | 'warning' | 'critical' | string;
  summary: AdminMarketplaceSummary;
  alerts: AdminMarketplaceAlert[];
  moderation: Record<string, unknown> & {
    status?: string;
    totals?: ModerationOverview['totals'];
    queues?: ModerationOverview['queues'];
    latest_cases?: ModerationCase[];
    active_risk_flags?: number;
    critical_risk_flags?: number;
  };
  trainer_onboarding: Record<string, unknown> & {
    status?: string;
    status_counts?: Array<{ status: string; count: number }>;
    submitted_without_case?: number;
    approved_without_role?: number;
    approved_without_profile?: number;
    under_review_count?: number;
    approved_count?: number;
  };
  payouts: Record<string, unknown> & {
    status?: string;
    overview?: AdminPayoutOverview;
    reconciliation?: Record<string, unknown>;
  };
  payments: Record<string, unknown> & {
    status?: string;
    statuses?: Array<{ status: string; count: number; amount?: string }>;
    failed_last_period?: number;
    paid_last_period?: number;
    recent_failed?: Payment[];
  };
  analytics: Record<string, unknown> & {
    status?: string;
    overview?: AnalyticsKpiOverview;
    warehouse_health?: AnalyticsWarehouseHealth;
  };
  reviews: Record<string, unknown> & {
    status?: string;
    pending_count?: number;
    latest_pending?: Review[];
  };
  audit: Record<string, unknown> & {
    status?: string;
    latest_events?: AuditEvent[];
    action_counts?: Array<{ event_type: string; count: number }>;
  };
  system: Record<string, unknown>;
};

export type TrainerBusinessReadinessCheck = {
  code: string;
  title: string;
  status: 'done' | 'warning' | 'blocker' | string;
};

export type TrainerBusinessDashboard = {
  generated_at: string;
  range_days: number;
  trainer_id: string;
  application: null | {
    id: string;
    status: string;
    brand_name?: string;
    legal_name?: string;
    submitted_at?: string | null;
    reviewed_at?: string | null;
    reviewer_note?: string;
    latest_moderation_case_id?: string | null;
  };
  profile: {
    legacy_profile?: null | Record<string, unknown>;
    public_profile?: null | Record<string, unknown>;
  };
  content: {
    drafts: { videos: number; programs: number; bundles: number; total: number };
    published: { videos: number; programs: number; bundles: number; total: number };
    draft_status_counts: Record<string, Array<{ status: string; count: number }>>;
    pending_review_count: number;
    latest_published: Array<{
      entity_type: string;
      id: string;
      slug: string;
      title: string;
      price_amount: string;
      currency: string;
      is_active: boolean;
      published_at?: string | null;
    }>;
  };
  commerce: {
    revenue_total: string;
    revenue_period: string;
    paid_orders_count: number;
    period_orders_count: number;
    customers_count: number;
    avg_order_value: string;
    order_items_count: number;
    order_items_period_count: number;
    revenue_series: Array<{ date: string; revenue: string; orders_count: number }>;
    top_products: Array<{ item_type: string; title: string; revenue: string; orders_count: number }>;
    latest_orders: Array<{
      id: string;
      status: string;
      total_amount: string;
      currency: string;
      paid_at?: string | null;
      completed_at?: string | null;
    }>;
  };
  payouts: {
    balance: {
      trainer_id: string;
      currency: string;
      available_amount: string;
      reserved_amount: string;
      lifetime_earned_amount: string;
      updated_at?: string | null;
    };
    status_counts: Array<{ status: string; count: number }>;
    requests_count: number;
    active_requests_count: number;
    latest_requests: Array<{
      id: string;
      amount: string;
      currency: string;
      status: string;
      destination_masked?: string;
      requested_at?: string | null;
      approved_at?: string | null;
      processed_at?: string | null;
      rejected_reason?: string;
    }>;
    can_request_payout: boolean;
  };
  moderation: {
    open_cases_count: number;
    risk_flags_count: number;
    critical_risk_flags_count: number;
    latest_cases: Array<Record<string, unknown>>;
  };
  readiness: {
    status: 'ready' | 'attention' | 'blocked' | string;
    checks: TrainerBusinessReadinessCheck[];
    blockers_count: number;
    warnings_count: number;
  };
};

export type CustomerHubContentRef = {
  id?: string;
  slug?: string;
  title?: string;
  description?: string;
  target_type?: string;
  trainer_slug?: string;
  trainer_name?: string;
  category?: string;
  difficulty?: string;
  duration_minutes?: number;
  price_amount?: string;
  currency?: string;
};

export type CustomerLibraryItem = {
  id: string;
  source_type?: string;
  source_order_id?: string | null;
  source_subscription_id?: string | null;
  target_type: string;
  target_id?: string | null;
  status: string;
  starts_at?: string | null;
  ends_at?: string | null;
  created_at?: string | null;
  metadata?: Record<string, unknown>;
  content?: CustomerHubContentRef;
  title?: string;
  trainer_name?: string;
  slug?: string;
  access_status?: string;
};

export type CustomerHubOrderItem = {
  id: string;
  item_type?: string;
  item_id?: string;
  title?: string;
  quantity?: number;
  unit_price?: string;
  total_price?: string;
  metadata?: Record<string, unknown>;
};

export type CustomerHubOrder = {
  id: string;
  order_type?: string;
  status?: string;
  currency?: string;
  total_amount?: string;
  created_at?: string | null;
  paid_at?: string | null;
  completed_at?: string | null;
  items_count?: number;
  items?: CustomerHubOrderItem[];
};

export type CustomerHubPaymentIssue = {
  id: string;
  order_id?: string;
  provider?: string;
  status?: string;
  amount?: string;
  currency?: string;
  created_at?: string | null;
};

export type CustomerHubSubscription = {
  id: string;
  status?: string;
  starts_at?: string | null;
  ends_at?: string | null;
  cancelled_at?: string | null;
  auto_renew?: boolean;
  plan?: SubscriptionPlan;
};

export type CustomerHubFavorite = {
  id: string;
  target_type: string;
  target_id: string;
  created_at?: string | null;
  title?: string;
  slug?: string;
  target?: CustomerHubContentRef & Record<string, unknown>;
};

export type CustomerHubReviewOpportunity = {
  target_type: string;
  target_id: string;
  title?: string;
  trainer_name?: string;
  slug?: string;
};

export type CustomerHubRecommendation = {
  target_type: string;
  target_id: string;
  slug: string;
  title: string;
  trainer_name?: string;
  trainer_slug?: string;
  category?: string;
  difficulty?: string;
  price_amount?: string;
  currency?: string;
  duration_minutes?: number;
  is_featured?: boolean;
};

export type CustomerMarketplaceHub = {
  profile: {
    id: string;
    display_name?: string;
    email?: string;
    bio?: string;
    streak_count?: number;
    active_role?: string;
    created_at?: string | null;
  };
  summary: {
    period_days: number;
    active_entitlements_count: number;
    active_subscriptions_count: number;
    paid_orders_count: number;
    orders_period_count: number;
    total_spent: string;
    period_spent: string;
    favorites_count: number;
    review_opportunities_count: number;
    failed_payments_count: number;
  };
  library: {
    summary: { total_count: number; active_count: number; by_type: Record<string, number> };
    items: CustomerLibraryItem[];
  };
  orders: {
    summary: {
      total_orders_count: number;
      paid_orders_count: number;
      orders_period_count: number;
      total_spent: string;
      period_spent: string;
    };
    recent: CustomerHubOrder[];
  };
  payments: {
    summary: { total_count: number; failed_count: number; pending_count: number };
    recent_failed: CustomerHubPaymentIssue[];
  };
  subscriptions: {
    summary: { total_count: number; active_count: number };
    items: CustomerHubSubscription[];
  };
  favorites: {
    summary: { total_count: number; by_type: Record<string, number> };
    items: CustomerHubFavorite[];
  };
  reviews: {
    summary: { reviews_count: number; review_opportunities_count: number };
    opportunities: CustomerHubReviewOpportunity[];
    recent: Array<Pick<Review, 'id' | 'target_type' | 'target_id' | 'rating' | 'title' | 'status' | 'created_at'>>;
  };
  recommendations: { items: CustomerHubRecommendation[] };
  readiness: {
    status: 'ready' | 'attention' | string;
    checks: Array<{ code: string; title: string; status: 'done' | 'todo' | 'optional' | 'attention' | string }>;
  };
};

export type AccessCenterItem = {
  id: string;
  source_type?: string;
  source_order_id?: string | null;
  source_subscription_id?: string | null;
  target_type: string;
  target_id?: string | null;
  status: string;
  is_available?: boolean;
  starts_at?: string | null;
  ends_at?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
  metadata?: Record<string, unknown>;
  content?: Record<string, unknown>;
  title?: string;
  trainer_name?: string;
  slug?: string;
  access_url?: string;
};

export type AccessCenterPayload = {
  summary: {
    period_days?: number;
    total_count: number;
    active_count: number;
    expired_count?: number;
    revoked_count?: number;
    expiring_soon_count?: number;
    library_access_active?: boolean;
    by_type?: Record<string, number>;
  };
  items: AccessCenterItem[];
  readiness?: Array<{ code: string; label: string; is_ok: boolean; severity?: string }>;
};

export type AccessDecision = {
  allowed: boolean;
  code: string;
  reason: string;
  target_type: string;
  target_id?: string | null;
  content?: Record<string, unknown>;
  entitlement_id?: string | null;
  source?: string | null;
};

export type TrainerApplicationStatus =
  | 'draft'
  | 'submitted'
  | 'under_review'
  | 'approved'
  | 'rejected'
  | 'changes_requested'
  | (string & {});

export interface TrainerApplicationPayload {
  brand_name?: string;
  contact_phone?: string;
  specialties?: string[];
  links?: string[];
  reviewer_note?: string | null;
  status?: TrainerApplicationStatus;
  legal_name?: string;
  display_name?: string;
  public_bio?: string;
  bio?: string;
  phone?: string;
  country?: string;
  city?: string;
  timezone?: string;
  preferred_language?: string;
  experience_years?: number | string | null;
  education?: string;
  certifications?: string[] | string;
  specializations?: string[] | string;
  website_url?: string;
  instagram_url?: string;
  telegram_url?: string;
  moderation_note?: string;
  documents?: unknown[];
  [key: string]: unknown;
}

export interface TrainerApplication extends TrainerApplicationPayload {
  brand_name?: string;
  contact_phone?: string;
  specialties?: string[];
  links?: string[];
  reviewer_note?: string | null;
  id: string;
  trainer_profile?: TrainerProfile | string | null;
  status: TrainerApplicationStatus;
  submitted_at?: string | null;
  reviewed_at?: string | null;
  review_comment?: string | null;
  rejection_reason?: string | null;
  created_at?: string;
  updated_at?: string;
}

export interface ProgramLessonDraft {
  id: string;
  program_id?: string | null;
  video_id?: string | null;
  video_asset_id?: string | null;
  title: string;
  description?: string;
  position: number;
  materials?: LessonMaterial[];
  duration_seconds?: number | null;
  is_preview?: boolean;
  created_at?: string;
  updated_at?: string;
  [key: string]: unknown;
}

export type LessonMaterial = {
  title: string;
  url?: string;
  asset_id?: string | null;
  kind?: 'link' | 'file' | 'pdf' | 'image' | string;
};

export interface CourseLessonDraft {
  id: string;
  course_id?: string | null;
  video_id?: string | null;
  video_asset_id?: string | null;
  title: string;
  description?: string;
  position: number;
  materials?: LessonMaterial[];
  duration_seconds?: number | null;
  is_preview?: boolean;
  created_at?: string;
  updated_at?: string;
  [key: string]: unknown;
}

export interface CourseDraft {
  id: string;
  title: string;
  slug: string;
  description: string;
  price_amount: string;
  currency: string;
  status?: string;
  metadata?: Record<string, unknown>;
  lessons?: CourseLessonDraft[];
  current_version_number?: number | null;
  created_at?: string;
  updated_at?: string;
  [key: string]: unknown;
}

export interface ProgramDraft {
  id: string;
  title: string;
  slug: string;
  description: string;
  price_amount: string;
  currency: string;
  status?: string;
  lessons?: ProgramLessonDraft[];
  current_version_number?: number | null;
  created_at?: string;
  updated_at?: string;
  [key: string]: unknown;
}

export interface BundleItemDraft {
  id: string;
  bundle_id?: string | null;
  item_type: 'video' | 'program' | string;
  target_id: string;
  object_id?: string | null;
  video_id?: string | null;
  program_id?: string | null;
  position: number;
  title?: string;
  name?: string;
  label?: string;
  target_title?: string;
  target_slug?: string;
  source_title?: string;
  price_override?: string | null;
  created_at?: string;
  updated_at?: string;
  [key: string]: unknown;
}

export interface BundleDraft {
  id: string;
  title: string;
  slug: string;
  description: string;
  price_amount: string;
  currency: string;
  status?: string;
  items?: BundleItemDraft[];
  current_version_number?: number | null;
  created_at?: string;
  updated_at?: string;
  [key: string]: unknown;
}

export type ContentRuntimeLesson = {
  id: string;
  lesson_id: string;
  slug?: string;
  title: string;
  description?: string;
  position: number;
  duration_minutes?: number;
  is_preview?: boolean;
  video_asset_id?: string | null;
  materials?: LessonMaterial[];
  created_at?: string | null;
  updated_at?: string | null;
};

export type ContentRuntimeAccess = {
  allowed: boolean;
  code: string;
  reason: string;
  target_type: string;
  target_id: string;
  entitlement_id?: string | null;
  source?: string | null;
  rules?: Array<Record<string, unknown>>;
  audit?: Record<string, unknown>;
};

export type ContentRuntimePayload = {
  allowed: boolean;
  blocked: boolean;
  runtime: 'program_lesson' | 'course_lesson' | string;
  lesson: ContentRuntimeLesson;
  program?: {
    id: string;
    program_id: string;
    slug: string;
    title: string;
    trainer_slug?: string;
    trainer_name?: string;
  };
  course?: {
    id: string;
    course_id: string;
    slug: string;
    title: string;
    metadata?: Record<string, unknown>;
  };
  access: ContentRuntimeAccess;
};

export type StudentLearningLesson = {
  id: string;
  lesson_id: string;
  program_id?: string;
  content_type?: 'program' | 'course' | string;
  title: string;
  description?: string;
  position: number;
  is_preview?: boolean;
  duration_minutes?: number;
  materials_count?: number;
  runtime_url: string;
  is_completed?: boolean;
  completed_at?: string | null;
};

export type StudentLearningMaterial = LessonMaterial & {
  lesson_id?: string;
  lesson_title?: string;
};

export type StudentLearningItem = {
  id: string;
  kind: 'course' | 'program' | 'video' | string;
  target_id: string;
  title: string;
  slug?: string;
  description?: string;
  trainer_name?: string;
  trainer_slug?: string;
  status: string;
  progress_percent: number;
  last_activity_at?: string | null;
  entitlement_id?: string;
  lessons: StudentLearningLesson[];
  materials: StudentLearningMaterial[];
  access_url?: string;
  access?: ContentRuntimeAccess;
  created_at?: string | null;
};

export type StudentLearningAreaPayload = {
  summary: {
    items_count: number;
    courses_count: number;
    programs_count: number;
    videos_count: number;
    lessons_count: number;
    materials_count: number;
    library_access?: boolean;
    unresolved_count?: number;
  };
  items: StudentLearningItem[];
  next_lesson?: StudentLearningLesson | null;
  materials: StudentLearningMaterial[];
  unresolved?: Array<Record<string, unknown>>;
};

export type AssignmentSubmission = {
  id: string;
  assignment_id: string;
  student_id: string;
  student_email?: string;
  answer_text: string;
  attachments?: Array<Record<string, unknown>>;
  status: 'submitted' | 'reviewed' | 'needs_revision' | 'approved' | string;
  submitted_at?: string | null;
  reviewed_at?: string | null;
  reviewed_by_id?: string | null;
  review_comment?: string;
  score?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
  assignment?: Assignment;
};

export type Assignment = {
  id: string;
  trainer_id: string;
  trainer_email?: string;
  title: string;
  description?: string;
  content_type: 'program' | 'course' | string;
  content_id: string;
  lesson_id?: string;
  due_at?: string | null;
  status: 'draft' | 'published' | 'archived' | string;
  metadata?: Record<string, unknown>;
  created_at?: string | null;
  updated_at?: string | null;
  submission?: AssignmentSubmission | null;
  submissions_count?: number;
  reviewed_count?: number;
  access?: {
    allowed: boolean;
    code?: string;
    reason?: string;
  };
};

export type AssignmentsPayload = {
  summary: {
    total: number;
    published?: number;
    draft?: number;
    submissions?: number;
    submitted?: number;
    pending?: number;
    needs_revision?: number;
    approved?: number;
  };
  items: Assignment[];
};

export type AssignmentSubmissionsPayload = {
  summary: {
    total: number;
    submitted?: number;
    needs_revision?: number;
    approved?: number;
  };
  items: AssignmentSubmission[];
};

export type AssignmentSubmitPayload = {
  answer_text?: string;
  attachments?: Array<Record<string, unknown>>;
};

export type AssignmentTrainerCreatePayload = {
  title: string;
  description?: string;
  content_type: 'program' | 'course';
  content_id: string;
  lesson_id?: string;
  due_at?: string | null;
  status?: 'draft' | 'published' | 'archived';
  metadata?: Record<string, unknown>;
};

export type AssignmentReviewPayload = {
  status?: 'reviewed' | 'needs_revision' | 'approved';
  review_comment?: string;
  score?: string | null;
};

export type Message = {
  id: string;
  conversation: string;
  sender?: string | null;
  sender_email?: string;
  message_type: 'user' | 'system' | string;
  body: string;
  delivery_status: string;
  metadata?: Record<string, unknown>;
  created_at?: string | null;
};

export type ConversationParticipant = {
  user_id: string;
  email?: string;
  role: string;
  unread_count: number;
};

export type Conversation = {
  id: string;
  kind: string;
  booking_reservation_id?: string | null;
  trainer_id?: string | null;
  client_id?: string | null;
  subject?: string;
  unread_count: number;
  last_message_at?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
  last_message?: Message | null;
  participants?: ConversationParticipant[];
  created_message?: Message;
};

export type MessagingInbox = {
  results: Conversation[];
  unread_total: number;
};
