"use client";

import { useTransition } from "react";
import { accountApi } from "@/lib/api";

export function RoleSwitcher({ roles, activeRole }: { roles: string[]; activeRole: string }) {
  const [pending, startTransition] = useTransition();

  return (
    <div className="flex flex-wrap gap-2">
      {roles.map((role) => (
        <button
          key={role}
          className={`rounded-xl border px-4 py-2 text-sm ${role === activeRole ? "bg-slate-900 text-white" : ""}`}
          disabled={pending}
          onClick={() =>
            startTransition(async () => {
              await accountApi.switchRole(role);
              window.location.reload();
            })
          }
        >
          {pending && role === activeRole ? "Switching..." : role}
        </button>
      ))}
    </div>
  );
}
