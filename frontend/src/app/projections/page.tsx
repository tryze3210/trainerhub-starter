import { projectionApi } from "@/lib/api";

export default async function ProjectionsPage() {
  const items = await projectionApi.statuses();

  return (
    <main className="p-8 space-y-6">
      <section>
        <h1 className="text-2xl font-semibold">Projection health</h1>
        <p className="text-sm text-gray-600">Read-model rebuild and lag visibility.</p>
      </section>
      <div className="grid gap-4">
        {items.map((item) => (
          <div key={item.projection_key} className="rounded-2xl border p-4">
            <div className="font-medium">{item.projection_key}</div>
            <div className="text-sm">Status: {item.status}</div>
            <div className="text-sm">Lag: {item.lag}</div>
            <div className="text-sm">Failed messages: {item.failed_messages}</div>
          </div>
        ))}
      </div>
    </main>
  );
}
