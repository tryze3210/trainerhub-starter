import { eventApi } from "@/lib/api";

export default async function EventsPage() {
  const [outbox, inbox] = await Promise.all([eventApi.outbox(), eventApi.inbox()]);

  return (
    <main className="p-8 space-y-8">
      <section>
        <h1 className="text-2xl font-semibold">Event bus</h1>
        <p className="text-sm text-gray-600">Outbox and inbox visibility for idempotent async processing.</p>
      </section>

      <section className="space-y-3">
        <h2 className="text-xl font-medium">Outbox</h2>
        <div className="grid gap-4">
          {outbox.map((item) => (
            <div key={item.id} className="rounded-2xl border p-4">
              <div className="font-medium">{item.topic}</div>
              <div className="text-sm">Status: {item.status}</div>
              <div className="text-sm">Attempts: {item.attempts}</div>
            </div>
          ))}
        </div>
      </section>

      <section className="space-y-3">
        <h2 className="text-xl font-medium">Inbox</h2>
        <div className="grid gap-4">
          {inbox.map((item) => (
            <div key={item.id} className="rounded-2xl border p-4">
              <div className="font-medium">{item.consumer}</div>
              <div className="text-sm">Message key: {item.message_key}</div>
              <div className="text-sm">Status: {item.status}</div>
            </div>
          ))}
        </div>
      </section>
    </main>
  );
}
