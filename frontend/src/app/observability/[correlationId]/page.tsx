import { observabilityApi } from "@/lib/api";

export default async function CorrelationDetailPage({ params }: { params: Promise<{ correlationId: string }> }) {
  const { correlationId } = await params;
  const item = await observabilityApi.correlation(correlationId);

  return (
    <main className="p-8 space-y-8">
      <section>
        <h1 className="text-2xl font-semibold">Correlation {item.correlation_id}</h1>
        <p className="text-sm text-gray-600">Unified troubleshooting view across events, workflows, logs and traces.</p>
      </section>

      <section className="rounded-2xl border p-4">
        <pre className="text-sm whitespace-pre-wrap">{JSON.stringify(item.summary, null, 2)}</pre>
      </section>

      <section className="grid lg:grid-cols-2 gap-4">
        <div className="rounded-2xl border p-4 space-y-3">
          <h2 className="text-lg font-medium">Logs</h2>
          {item.logs.map((log) => (
            <div key={log.id} className="text-sm border-t pt-3 first:border-t-0 first:pt-0">
              <div className="font-medium">{log.level} · {log.service}</div>
              <div>{log.message}</div>
            </div>
          ))}
        </div>
        <div className="rounded-2xl border p-4 space-y-3">
          <h2 className="text-lg font-medium">Traces</h2>
          {item.traces.map((trace) => (
            <div key={trace.span_id} className="text-sm border-t pt-3 first:border-t-0 first:pt-0">
              <div className="font-medium">{trace.operation}</div>
              <div>{trace.service} · {trace.duration_ms} ms</div>
            </div>
          ))}
        </div>
      </section>
    </main>
  );
}
