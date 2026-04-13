import { accessApi } from "@/lib/api";
import { ObjectCheckForm } from "./object-check-form";

export default async function ObjectAccessPage() {
  const allowed = await accessApi.checkObject({ object_type: "trainer_content", object_id: "vid_anna_core_01", action: "edit" });
  const denied = await accessApi.checkObject({ object_type: "trainer_content", object_id: "vid_other_01", action: "edit" });

  return (
    <main className="p-8 space-y-6">
      <section>
        <h1 className="text-3xl font-semibold">Object access</h1>
        <p className="text-sm text-gray-600">Object-level authorization with tenant boundary and ownership checks.</p>
      </section>

      <section className="grid md:grid-cols-2 gap-4">
        {[allowed, denied].map((item) => (
          <article key={`${item.object_type}-${item.object_id}-${item.code}`} className="border rounded-xl p-4 space-y-2">
            <div className="flex items-center justify-between">
              <h2 className="font-medium">{item.object_type}:{item.object_id}</h2>
              <span>{item.allowed ? "allowed" : "blocked"}</span>
            </div>
            <div className="text-sm text-gray-600">Action: {item.action}</div>
            <div className="text-sm text-gray-600">Reason: {item.reason}</div>
            <div className="text-sm text-gray-600">Tenant: {item.tenant_id ?? "—"}</div>
            <div className="text-sm text-gray-600">Owner: {item.owner_account_id ?? "—"}</div>
            <div className="text-sm text-gray-600">Actor role: {item.actor_role ?? "—"}</div>
          </article>
        ))}
      </section>

      <ObjectCheckForm />
    </main>
  );
}
