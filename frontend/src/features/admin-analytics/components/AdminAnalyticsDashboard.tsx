"use client";

import { useEffect, useMemo, useState } from "react";
import { Bar, BarChart, CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import {
  fetchFunnelSeries,
  fetchKPIOverview,
  fetchRetentionCohorts,
  fetchRevenueSeries,
  fetchTopTrainers,
  fetchTrafficAttribution,
  fetchTrafficSeries,
  fetchTrafficTopPaths,
  fetchWarehouseHealth,
} from "../api";
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
} from "../types";

type DashboardState = {
  overview: KPIOverview | null;
  revenueSeries: RevenueSeriesPoint[];
  topTrainers: TopTrainer[];
  funnelSeries: FunnelPoint[];
  retention: CohortRetention[];
  health: WarehouseHealth | null;
  trafficSeries: TrafficPoint[];
  topPaths: TopPath[];
  attribution: AttributionRow[];
};

const rangeOptions = [7, 30, 90];

function formatMoney(value: string | number) {
  return new Intl.NumberFormat("ru-RU", {
    style: "currency",
    currency: "EUR",
    maximumFractionDigits: 2,
  }).format(Number(value));
}

function formatPercent(value: string | number) {
  return `${(Number(value) * 100).toFixed(2)}%`;
}

export function AdminAnalyticsDashboard() {
  const [days, setDays] = useState(30);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<TrafficFilters>({});
  const [draftFilters, setDraftFilters] = useState<TrafficFilters>({});
  const [state, setState] = useState<DashboardState>({
    overview: null,
    revenueSeries: [],
    topTrainers: [],
    funnelSeries: [],
    retention: [],
    health: null,
    trafficSeries: [],
    topPaths: [],
    attribution: [],
  });

  useEffect(() => {
    let mounted = true;

    async function load() {
      try {
        setLoading(true);
        setError(null);

        const [overview, revenueSeries, topTrainers, funnelSeries, retention, health, trafficSeries, topPaths, attribution] = await Promise.all([
          fetchKPIOverview(days),
          fetchRevenueSeries(days),
          fetchTopTrainers(days, 10),
          fetchFunnelSeries(days),
          fetchRetentionCohorts(Math.max(days, 60)),
          fetchWarehouseHealth(),
          fetchTrafficSeries(days, filters),
          fetchTrafficTopPaths(days, filters, 10),
          fetchTrafficAttribution(days, filters, 10),
        ]);

        if (!mounted) return;
        setState({ overview, revenueSeries, topTrainers, funnelSeries, retention, health, trafficSeries, topPaths, attribution });
      } catch (err) {
        if (!mounted) return;
        setError(err instanceof Error ? err.message : "Failed to load analytics dashboard.");
      } finally {
        if (mounted) setLoading(false);
      }
    }

    load();
    return () => {
      mounted = false;
    };
  }, [days, filters]);

  const revenueChartData = useMemo(
    () => state.revenueSeries.map((point) => ({ ...point, paid_revenue_number: Number(point.paid_revenue) })),
    [state.revenueSeries],
  );

  const funnelChartData = useMemo(
    () => state.funnelSeries.map((point) => ({ date: point.date, signups: point.signups, paid_customers: point.paid_customers, new_subscribers: point.new_subscribers })),
    [state.funnelSeries],
  );

  const trafficChartData = useMemo(
    () => state.trafficSeries.map((point) => ({ ...point })),
    [state.trafficSeries],
  );

  if (loading) {
    return <div className="rounded-2xl border border-zinc-800 bg-zinc-950 p-6 text-zinc-200">Loading analytics...</div>;
  }

  if (error) {
    return <div className="rounded-2xl border border-red-900 bg-red-950/30 p-6 text-red-200">{error}</div>;
  }

  if (!state.overview) {
    return <div className="rounded-2xl border border-zinc-800 bg-zinc-950 p-6 text-zinc-200">No analytics data yet.</div>;
  }

  const overview = state.overview;

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 rounded-3xl border border-zinc-800 bg-zinc-950 p-6 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-white">Analytics dashboard</h1>
          <p className="mt-1 text-sm text-zinc-400">Last aggregated date: {overview.last_aggregated_date ?? "not available"}</p>
        </div>

        <div className="flex gap-2">
          {rangeOptions.map((option) => (
            <button
              key={option}
              onClick={() => setDays(option)}
              className={`rounded-2xl px-4 py-2 text-sm font-medium transition ${days === option ? "bg-white text-zinc-900" : "border border-zinc-700 bg-zinc-900 text-zinc-300 hover:bg-zinc-800"}`}
            >
              {option}d
            </button>
          ))}
        </div>
      </div>

      <section className="rounded-3xl border border-zinc-800 bg-zinc-950 p-6">
        <div className="mb-4">
          <h2 className="text-lg font-semibold text-white">Traffic drill-down</h2>
          <p className="text-sm text-zinc-400">Filter materialized traffic slices by attribution, trainer and page path.</p>
        </div>

        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-5">
          <FilterInput label="Source" value={draftFilters.source ?? ""} onChange={(value) => setDraftFilters((prev) => ({ ...prev, source: value }))} />
          <FilterInput label="Medium" value={draftFilters.medium ?? ""} onChange={(value) => setDraftFilters((prev) => ({ ...prev, medium: value }))} />
          <FilterInput label="Campaign" value={draftFilters.campaign ?? ""} onChange={(value) => setDraftFilters((prev) => ({ ...prev, campaign: value }))} />
          <FilterInput label="Trainer ID" value={draftFilters.trainer_id ?? ""} onChange={(value) => setDraftFilters((prev) => ({ ...prev, trainer_id: value }))} />
          <FilterInput label="Path prefix" value={draftFilters.path_prefix ?? ""} onChange={(value) => setDraftFilters((prev) => ({ ...prev, path_prefix: value }))} />
        </div>

        <div className="mt-4 flex gap-3">
          <button onClick={() => setFilters(draftFilters)} className="rounded-2xl bg-white px-4 py-2 text-sm font-medium text-zinc-900">Apply filters</button>
          <button onClick={() => { setDraftFilters({}); setFilters({}); }} className="rounded-2xl border border-zinc-700 bg-zinc-900 px-4 py-2 text-sm text-zinc-300">Reset</button>
        </div>
      </section>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard title="Paid revenue" value={formatMoney(overview.revenue)} />
        <MetricCard title="Gross revenue" value={formatMoney(overview.gross_revenue)} />
        <MetricCard title="Paid orders" value={String(overview.paid_orders)} />
        <MetricCard title="Conversion" value={formatPercent(overview.conversion_rate)} />
        <MetricCard title="New customers" value={String(overview.new_customers)} />
        <MetricCard title="New trainers" value={String(overview.new_trainers)} />
        <MetricCard title="New subscriptions" value={String(overview.new_subscriptions)} />
        <MetricCard title="ARPPU" value={formatMoney(overview.arppu)} />
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.7fr_1fr]">
        <section className="rounded-3xl border border-zinc-800 bg-zinc-950 p-6">
          <div className="mb-4">
            <h2 className="text-lg font-semibold text-white">Revenue trend</h2>
            <p className="text-sm text-zinc-400">Paid revenue by day</p>
          </div>
          <div className="h-[320px]">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={revenueChartData}>
                <CartesianGrid vertical={false} strokeDasharray="3 3" />
                <XAxis dataKey="date" stroke="currentColor" className="text-zinc-500" />
                <YAxis stroke="currentColor" className="text-zinc-500" />
                <Tooltip />
                <Line type="monotone" dataKey="paid_revenue_number" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </section>

        <section className="rounded-3xl border border-zinc-800 bg-zinc-950 p-6">
          <div className="mb-4">
            <h2 className="text-lg font-semibold text-white">Warehouse health</h2>
            <p className="text-sm text-zinc-400">Last successful materialization snapshot</p>
          </div>
          <div className="space-y-4">
            <MetricRow label="Status" value={state.health?.status ?? "unknown"} />
            <MetricRow label="Rows written" value={String(state.health?.last_success_rows_written ?? 0)} />
            <MetricRow label="Last range" value={state.health?.last_success_range_start && state.health?.last_success_range_end ? `${state.health.last_success_range_start} → ${state.health.last_success_range_end}` : "n/a"} />
            <MetricRow label="Failure" value={state.health?.latest_failure_message || "none"} />
          </div>
        </section>
      </div>

      <div className="grid gap-6 xl:grid-cols-2">
        <section className="rounded-3xl border border-zinc-800 bg-zinc-950 p-6">
          <div className="mb-4">
            <h2 className="text-lg font-semibold text-white">Traffic trend</h2>
            <p className="text-sm text-zinc-400">Sessions and page views by day for current drill-down filters.</p>
          </div>
          <div className="h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={trafficChartData}>
                <CartesianGrid vertical={false} strokeDasharray="3 3" />
                <XAxis dataKey="date" stroke="currentColor" className="text-zinc-500" />
                <YAxis stroke="currentColor" className="text-zinc-500" />
                <Tooltip />
                <Line type="monotone" dataKey="sessions" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="page_views" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="purchases" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </section>

        <section className="rounded-3xl border border-zinc-800 bg-zinc-950 p-6">
          <div className="mb-4">
            <h2 className="text-lg font-semibold text-white">Acquisition funnel</h2>
            <p className="text-sm text-zinc-400">Signups → paid customers → subscribers</p>
          </div>
          <div className="h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={funnelChartData}>
                <CartesianGrid vertical={false} strokeDasharray="3 3" />
                <XAxis dataKey="date" stroke="currentColor" className="text-zinc-500" />
                <YAxis stroke="currentColor" className="text-zinc-500" />
                <Tooltip />
                <Bar dataKey="signups" radius={[8, 8, 0, 0]} />
                <Bar dataKey="paid_customers" radius={[8, 8, 0, 0]} />
                <Bar dataKey="new_subscribers" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </section>
      </div>

      <div className="grid gap-6 xl:grid-cols-2">
        <section className="rounded-3xl border border-zinc-800 bg-zinc-950 p-6">
          <div className="mb-4">
            <h2 className="text-lg font-semibold text-white">Top paths</h2>
            <p className="text-sm text-zinc-400">Highest traffic landing and content pages for the current slice.</p>
          </div>
          <SimpleTable
            headers={["Path", "Sessions", "Page views", "Video views", "Checkouts", "Purchases"]}
            rows={state.topPaths.map((row) => [row.path, row.sessions, row.page_views, row.video_views, row.checkout_starts, row.purchases])}
          />
        </section>

        <section className="rounded-3xl border border-zinc-800 bg-zinc-950 p-6">
          <div className="mb-4">
            <h2 className="text-lg font-semibold text-white">Attribution</h2>
            <p className="text-sm text-zinc-400">Source / medium / campaign performance for the current slice.</p>
          </div>
          <SimpleTable
            headers={["Source", "Medium", "Campaign", "Sessions", "Page views", "Purchases"]}
            rows={state.attribution.map((row) => [row.utm_source, row.utm_medium, row.utm_campaign, row.sessions, row.page_views, row.purchases])}
          />
        </section>
      </div>

      <div className="grid gap-6 xl:grid-cols-2">
        <section className="rounded-3xl border border-zinc-800 bg-zinc-950 p-6">
          <div className="mb-4">
            <h2 className="text-lg font-semibold text-white">Recent cohorts</h2>
            <p className="text-sm text-zinc-400">Retention by signup date</p>
          </div>
          <SimpleTable
            headers={["Cohort", "Size", "D1", "D7", "D30"]}
            rows={state.retention.slice(-10).reverse().map((row) => [row.cohort_date, row.cohort_size, formatPercent(row.retention_day_1_rate), formatPercent(row.retention_day_7_rate), formatPercent(row.retention_day_30_rate)])}
          />
        </section>

        <section className="rounded-3xl border border-zinc-800 bg-zinc-950 p-6">
          <div className="mb-4">
            <h2 className="text-lg font-semibold text-white">Top trainers</h2>
            <p className="text-sm text-zinc-400">Highest paid revenue in the selected period</p>
          </div>
          <SimpleTable
            headers={["Trainer", "Revenue", "Paid orders", "Customers", "Subscribers"]}
            rows={state.topTrainers.map((row) => [row.trainer_id, formatMoney(row.paid_revenue), row.paid_orders, row.new_customers, row.active_subscribers])}
          />
        </section>
      </div>
    </div>
  );
}

function FilterInput({ label, value, onChange }: { label: string; value: string; onChange: (value: string) => void }) {
  return (
    <label className="block">
      <span className="mb-2 block text-xs uppercase tracking-wide text-zinc-500">{label}</span>
      <input value={value} onChange={(event) => onChange(event.target.value)} className="w-full rounded-2xl border border-zinc-700 bg-zinc-900 px-4 py-2 text-sm text-zinc-100 outline-none placeholder:text-zinc-500" />
    </label>
  );
}

function MetricCard({ title, value }: { title: string; value: string }) {
  return (
    <div className="rounded-3xl border border-zinc-800 bg-zinc-950 p-5">
      <p className="text-sm text-zinc-400">{title}</p>
      <p className="mt-3 text-2xl font-semibold text-white">{value}</p>
    </div>
  );
}

function MetricRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-start justify-between gap-4 border-b border-zinc-900 pb-3 text-sm last:border-none last:pb-0">
      <span className="text-zinc-500">{label}</span>
      <span className="max-w-[65%] text-right text-zinc-100">{value}</span>
    </div>
  );
}

function SimpleTable({ headers, rows }: { headers: Array<string>; rows: Array<Array<string | number>> }) {
  return (
    <div className="overflow-x-auto">
      <table className="min-w-full text-sm text-zinc-300">
        <thead>
          <tr className="border-b border-zinc-800 text-left text-zinc-500">
            {headers.map((header) => (
              <th key={header} className="px-3 py-3">{header}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr key={`${row[0]}-${index}`} className="border-b border-zinc-900/80 align-top">
              {row.map((cell, cellIndex) => (
                <td key={cellIndex} className="px-3 py-3">{cell}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
