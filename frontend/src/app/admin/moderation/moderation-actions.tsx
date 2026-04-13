"use client";

import { useTransition } from "react";
import { moderationApi } from "@/lib/api";

export function ModerationActions({ id }: { id: string }) {
  const [pending, startTransition] = useTransition();

  return (
    <div className="mt-4 flex gap-2">
      <button
        className="rounded-xl border px-4 py-2 text-sm"
        disabled={pending}
        onClick={() => startTransition(async () => { await moderationApi.approve(id); window.location.reload(); })}
      >
        Approve
      </button>
      <button
        className="rounded-xl border px-4 py-2 text-sm"
        disabled={pending}
        onClick={() => startTransition(async () => { await moderationApi.reject(id, "Rejected by admin"); window.location.reload(); })}
      >
        Reject
      </button>
    </div>
  );
}
