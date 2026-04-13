"use client";

import { useTransition } from "react";
import { onboardingApi } from "@/lib/api";

export function CompleteStepButton({ code }: { code: string }) {
  const [pending, startTransition] = useTransition();

  return (
    <button
      className="rounded-xl border px-4 py-2 text-sm"
      disabled={pending}
      onClick={() =>
        startTransition(async () => {
          await onboardingApi.completeStep(code, { source: "frontend-demo" });
          window.location.reload();
        })
      }
    >
      {pending ? "Saving..." : "Mark complete"}
    </button>
  );
}
