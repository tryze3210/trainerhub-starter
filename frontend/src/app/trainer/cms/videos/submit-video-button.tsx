"use client";

import { useTransition } from "react";
import { trainerCmsApi } from "@/lib/api";

export function SubmitVideoButton({ id }: { id: string }) {
  const [pending, startTransition] = useTransition();

  return (
    <button
      className="rounded-xl border px-4 py-2 text-sm"
      disabled={pending}
      onClick={() => startTransition(async () => { await trainerCmsApi.submitVideo(id); window.location.reload(); })}
    >
      {pending ? "Submitting..." : "Submit for review"}
    </button>
  );
}
