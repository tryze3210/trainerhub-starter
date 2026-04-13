import Link from "next/link";
import { accessApi } from "@/lib/api";

export default async function AccessPage() {
  const snapshot = await accessApi.snapshot();
  const entries = Object.values(snapshot.feature_gates);

  return (
    <main className="p-8 space-y-6">
      <section>
        <h1 className="text-3xl font-semibold">Access matrix</h1>
        <p className="text-sm text-gray-600">Role, tenant, capabilities and feature gates resolved by backend policy layer.</p>
      </section>

      <section className="border rounded-xl p-4 space-y-2">
        <div><strong>Active role:</strong> {snapshot.account.active_role}</div>
        <div><strong>Available roles:</strong> {snapshot.account.available_roles.join(", ")}</div>
        <div><strong>Active tenant:</strong> {snapshot.tenant.name} ({snapshot.tenant.code})</div>
        <div><strong>Tenant permissions:</strong> {snapshot.tenant.permissions.join(", ")}</div>
        <div><strong>Capabilities:</strong> {snapshot.capabilities.join(", ")}</div>
        <div><strong>Completed onboarding steps:</strong> {snapshot.completed_steps.join(", ") || "—"}</div>
      </section>

      <section className="space-y-3">
        {entries.map((gate) => (
          <article key={gate.key} className="border rounded-xl p-4 space-y-2">
            <div className="flex items-center justify-between">
              <h2 className="font-medium">{gate.key}</h2>
              <span>{gate.enabled ? "enabled" : "blocked"}</span>
            </div>
            <div className="text-sm text-gray-600">Reason: {gate.reason}</div>
            <div className="text-sm text-gray-600">Required role: {gate.required_role ?? "—"}</div>
            <div className="text-sm text-gray-600">Missing steps: {gate.required_onboarding_steps.join(", ") || "—"}</div>
          </article>
        ))}
      </section>

      <nav className="flex gap-4 text-sm underline">
        <Link href="/tenancy">Tenant context</Link>
        <Link href="/object-access">Object access</Link>
        <Link href="/cabinet">Cabinet</Link>
        <Link href="/trainer/cms">Trainer CMS</Link>
        <Link href="/admin/moderation">Moderation</Link>
      </nav>
    </main>
  );
}
