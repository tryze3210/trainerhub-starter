import Link from "next/link";
import { tenancyApi } from "@/lib/api";
import { TenantSwitcher } from "./tenant-switcher";

export default async function TenancyPage() {
  const context = await tenancyApi.context();

  return (
    <main className="p-8 space-y-6">
      <section>
        <h1 className="text-3xl font-semibold">Tenant context</h1>
        <p className="text-sm text-gray-600">Active tenant boundary, memberships and ownership scope resolved by backend.</p>
      </section>

      <section className="border rounded-xl p-4 space-y-2">
        <div><strong>Active tenant:</strong> {context.active_tenant.name}</div>
        <div><strong>Code:</strong> {context.active_tenant.code}</div>
        <div><strong>Kind:</strong> {context.active_tenant.kind}</div>
        <div><strong>Membership role:</strong> {context.active_tenant.membership_role}</div>
        <div><strong>Permissions:</strong> {context.active_tenant.permissions.join(", ")}</div>
      </section>

      <TenantSwitcher memberships={context.memberships} activeTenantCode={context.active_tenant.code} />

      <section className="space-y-3">
        {context.memberships.map((membership) => (
          <article key={membership.tenant_id} className="border rounded-xl p-4 space-y-1">
            <h2 className="font-medium">{membership.tenant_name}</h2>
            <div className="text-sm text-gray-600">{membership.tenant_code} · {membership.tenant_kind}</div>
            <div className="text-sm text-gray-600">Role: {membership.membership_role} · Status: {membership.status}</div>
            <div className="text-sm text-gray-600">Permissions: {membership.permissions.join(", ")}</div>
          </article>
        ))}
      </section>

      <nav className="flex gap-4 text-sm underline">
        <Link href="/access">Access snapshot</Link>
        <Link href="/object-access">Object access</Link>
        <Link href="/trainer/cms">Trainer CMS</Link>
      </nav>
    </main>
  );
}
