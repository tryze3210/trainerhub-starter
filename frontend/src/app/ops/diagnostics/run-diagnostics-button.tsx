"use client";

import { useTransition } from "react";

import { opsApi } from "@/lib/api";

export function RunDiagnosticsButton({ suiteKey }: { suiteKey: string }) {
  const [pending, startTransition] = useTransition();

  return (
    <button
      className="rounded-xl border px-4 py-2 text-sm hover:bg-gray-50 disabled:opacity-60"
      disabled={pending}
      onClick={() => {
        startTransition(async () => {
          await opsApi.runDiagnostics({ suite_key: suiteKey });
          window.location.reload();
        });
      }}
    >
      {pending ? "Running..." : "Run diagnostics"}
    </button>
  );
}
