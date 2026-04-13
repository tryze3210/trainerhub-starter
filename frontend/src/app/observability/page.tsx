import Link from "next/link";

import { observabilityApi } from "@/lib/api";

export default async function ObservabilityPage() {
  const [overview, metrics, logs, traces] = await Promise.all([
    observabilityApi.overview(),
    observabilityApi.metrics(),
    observabilityApi.logs(),
    observabilityApi.traces(),
  ]);

  return (
    <main className="p-8 space-y-8">
      <section>
        <h1 className="text-2xl font-semibold">Observability</h1>
        <p className="text-sm text-gray-600">Metrics, logs, traces and correlation-aware platform health.</p>
      </section>

      <section className="rounded-2xl border p-4 space-y-2">
        <div className="font-medium">Platform health: {overview.platform_health}</div>
        <div className="text-sm text-gray-600">Error budget remaining: {overview.error_budget.remaining_percent}%</div>
        <div className="text-sm">Counters: metrics {overview.counters.metrics}, logs {overview.counters.logs}, traces {overview.counters.traces}</div>
        <div className="flex flex-wrap gap-2 pt-2">
          {overview.hot_correlations.map((item) => (
            <Link key={item} href={`/observability/${item}`} className="rounded-full border px-3 py-1 text-sm hover:bg-gray-50">
              {item}
            </Link>
          ))}
        </div>
      </section>

      <section className="grid lg:grid-cols-3 gap-4">
        <div className="rounded-2xl border p-4 space-y-3">
          <h2 className="text-lg font-medium">Metrics</h2>
          {metrics.map((item) => (
            <div key={item.key} className="text-sm border-t pt-3 first:border-t-0 first:pt-0">
              <div className="font-medium">{item.key}</div>
              <div>{item.value} {item.unit}</div>
              <div className="text-gray-600">Status: {item.status}</div>
            </div>
          ))}
        </div>

        <div className="rounded-2xl border p-4 space-y-3">
          <h2 className="text-lg font-medium">Logs</h2>
          {logs.map((item) => (
            <div key={item.id} className="text-sm border-t pt-3 first:border-t-0 first:pt-0">
              <div className="font-medium">{item.level} · {item.service}</div>
              <div>{item.message}</div>
              {item.correlation_id ? <div className="text-gray-600">Correlation: {item.correlation_id}</div> : null}
            </div>
          ))}
        </div>

        <div className="rounded-2xl border p-4 space-y-3">
          <h2 className="text-lg font-medium">Traces</h2>
          {traces.map((item) => (
            <div key={item.span_id} className="text-sm border-t pt-3 first:border-t-0 first:pt-0">
              <div className="font-medium">{item.operation}</div>
              <div>{item.service} · {item.duration_ms} ms</div>
              <div className="text-gray-600">Status: {item.status}</div>
            </div>
          ))}
        </div>
      </section>
    </main>
  );
}
