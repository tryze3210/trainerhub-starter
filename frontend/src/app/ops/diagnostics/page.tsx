import { opsApi } from "@/lib/api";

import { RunDiagnosticsButton } from "./run-diagnostics-button";

export default async function DiagnosticsPage() {
  const snapshot = await opsApi.diagnostics();

  return (
    <main className="p-8 space-y-8">
      <section className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold">Ops diagnostics</h1>
          <p className="text-sm text-gray-600">Controlled health checks for platform operations and admin troubleshooting.</p>
        </div>
        <RunDiagnosticsButton suiteKey="platform_health" />
      </section>

      <section className="rounded-2xl border p-4">
        <div className="font-medium">Overall status: {snapshot.overall_status}</div>
      </section>

      <section className="grid lg:grid-cols-2 gap-4">
        <div className="rounded-2xl border p-4 space-y-3">
          <h2 className="text-lg font-medium">Checks</h2>
          {snapshot.checks.map((item) => (
            <div key={item.key} className="text-sm border-t pt-3 first:border-t-0 first:pt-0">
              <div className="font-medium">{item.title}</div>
              <div>{item.message}</div>
              <div className="text-gray-600">{item.status} · severity {item.severity} · owner {item.owner}</div>
            </div>
          ))}
        </div>

        <div className="rounded-2xl border p-4 space-y-3">
          <h2 className="text-lg font-medium">Recent runs</h2>
          {snapshot.recent_runs.length === 0 ? <p className="text-sm text-gray-600">No diagnostic runs yet.</p> : null}
          {snapshot.recent_runs.map((item) => (
            <div key={item.id} className="text-sm border-t pt-3 first:border-t-0 first:pt-0">
              <div className="font-medium">{item.suite_key}</div>
              <div>{item.status}</div>
              <div className="text-gray-600">Triggered by {item.triggered_by}</div>
            </div>
          ))}
        </div>
      </section>
    </main>
  );
}
