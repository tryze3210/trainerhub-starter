"use client";

import { useState } from "react";
import { accessApi, ObjectDecision } from "@/lib/api";

export function ObjectCheckForm() {
  const [result, setResult] = useState<ObjectDecision | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(formData: FormData) {
    setLoading(true);
    try {
      const payload = {
        object_type: String(formData.get("object_type") || "trainer_content"),
        object_id: String(formData.get("object_id") || "vid_anna_core_01"),
        action: String(formData.get("action") || "edit"),
      };
      const response = await accessApi.checkObject(payload);
      setResult(response);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="border rounded-xl p-4 space-y-4">
      <h2 className="font-medium">Manual object check</h2>
      <form action={onSubmit} className="grid md:grid-cols-4 gap-3">
        <input name="object_type" defaultValue="trainer_content" className="border rounded-lg px-3 py-2" />
        <input name="object_id" defaultValue="vid_anna_core_01" className="border rounded-lg px-3 py-2" />
        <input name="action" defaultValue="edit" className="border rounded-lg px-3 py-2" />
        <button type="submit" disabled={loading} className="bg-black text-white rounded-lg px-4 py-2">
          {loading ? "Checking..." : "Check"}
        </button>
      </form>
      {result ? (
        <div className="text-sm text-gray-700 space-y-1">
          <div><strong>Decision:</strong> {result.allowed ? "allowed" : "blocked"}</div>
          <div><strong>Code:</strong> {result.code}</div>
          <div><strong>Reason:</strong> {result.reason}</div>
        </div>
      ) : null}
    </section>
  );
}
