"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { tenancyApi, TenantMembership } from "@/lib/api";

export function TenantSwitcher({ memberships, activeTenantCode }: { memberships: TenantMembership[]; activeTenantCode: string }) {
  const [tenantCode, setTenantCode] = useState(activeTenantCode);
  const [pending, setPending] = useState(false);
  const router = useRouter();

  async function onSubmit(formData: FormData) {
    const value = String(formData.get("tenant_code") || activeTenantCode);
    setPending(true);
    try {
      await tenancyApi.switchTenant(value);
      router.refresh();
    } finally {
      setPending(false);
    }
  }

  return (
    <form action={onSubmit} className="border rounded-xl p-4 flex items-end gap-3">
      <label className="flex flex-col gap-2 text-sm">
        Active tenant
        <select
          name="tenant_code"
          value={tenantCode}
          onChange={(e) => setTenantCode(e.target.value)}
          className="border rounded-lg px-3 py-2 min-w-72"
        >
          {memberships.map((membership) => (
            <option key={membership.tenant_id} value={membership.tenant_code}>
              {membership.tenant_name} ({membership.membership_role})
            </option>
          ))}
        </select>
      </label>
      <button type="submit" disabled={pending} className="bg-black text-white rounded-lg px-4 py-2">
        {pending ? "Switching..." : "Switch tenant"}
      </button>
    </form>
  );
}
