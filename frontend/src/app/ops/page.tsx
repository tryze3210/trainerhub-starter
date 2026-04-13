import Link from "next/link";

export default function OpsPage() {
  return (
    <main className="p-8 space-y-6">
      <section>
        <h1 className="text-2xl font-semibold">Operations</h1>
        <p className="text-sm text-gray-600">Diagnostics and platform operations visibility.</p>
      </section>
      <Link href="/ops/diagnostics" className="rounded-2xl border p-4 block hover:bg-gray-50">
        <div className="font-medium">Diagnostics</div>
        <div className="text-sm text-gray-600">Run controlled health checks and inspect recent results.</div>
      </Link>
    </main>
  );
}
