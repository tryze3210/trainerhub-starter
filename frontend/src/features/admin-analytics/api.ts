import {
  AttributionRow,
  CohortRetention,
  FunnelPoint,
  KPIOverview,
  RevenueSeriesPoint,
  TopPath,
  TopTrainer,
  TrafficFilters,
  TrafficPoint,
  WarehouseHealth,
} from './types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL;

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
    },
    cache: 'no-store',
  });

  if (!response.ok) {
    throw new Error(`Analytics API request failed: ${response.status}`);
  }

  return response.json() as Promise<T>;
}

function toQuery(filters: TrafficFilters = {}, days = 30, limit?: number): string {
  const params = new URLSearchParams({ days: String(days) });
  if (limit) params.set('limit', String(limit));
  if (filters.source) params.set('source', filters.source);
  if (filters.medium) params.set('medium', filters.medium);
  if (filters.campaign) params.set('campaign', filters.campaign);
  if (filters.trainer_id) params.set('trainer_id', filters.trainer_id);
  if (filters.path_prefix) params.set('path_prefix', filters.path_prefix);
  return params.toString();
}

export function fetchKPIOverview(days = 30): Promise<KPIOverview> {
  return getJson<KPIOverview>(`/api/v1/admin/analytics/overview/?days=${days}`);
}

export function fetchRevenueSeries(days = 30): Promise<RevenueSeriesPoint[]> {
  return getJson<RevenueSeriesPoint[]>(`/api/v1/admin/analytics/revenue-timeseries/?days=${days}`);
}

export function fetchTopTrainers(days = 30, limit = 10): Promise<TopTrainer[]> {
  return getJson<TopTrainer[]>(`/api/v1/admin/analytics/top-trainers/?days=${days}&limit=${limit}`);
}

export function fetchFunnelSeries(days = 30): Promise<FunnelPoint[]> {
  return getJson<FunnelPoint[]>(`/api/v1/admin/analytics/funnel-timeseries/?days=${days}`);
}

export function fetchRetentionCohorts(days = 60): Promise<CohortRetention[]> {
  return getJson<CohortRetention[]>(`/api/v1/admin/analytics/retention-cohorts/?days=${days}`);
}

export function fetchWarehouseHealth(): Promise<WarehouseHealth> {
  return getJson<WarehouseHealth>(`/api/v1/admin/analytics/warehouse-health/`);
}

export function fetchTrafficSeries(days = 30, filters: TrafficFilters = {}): Promise<TrafficPoint[]> {
  return getJson<TrafficPoint[]>(`/api/v1/admin/analytics/traffic-timeseries/?${toQuery(filters, days)}`);
}

export function fetchTrafficTopPaths(days = 30, filters: TrafficFilters = {}, limit = 10): Promise<TopPath[]> {
  return getJson<TopPath[]>(`/api/v1/admin/analytics/traffic-top-paths/?${toQuery(filters, days, limit)}`);
}

export function fetchTrafficAttribution(days = 30, filters: TrafficFilters = {}, limit = 10): Promise<AttributionRow[]> {
  return getJson<AttributionRow[]>(`/api/v1/admin/analytics/traffic-attribution/?${toQuery(filters, days, limit)}`);
}
