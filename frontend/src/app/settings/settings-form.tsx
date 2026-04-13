"use client";

import { FormEvent, useState } from "react";
import { AccountSettings, accountApi } from "@/lib/api";

export function SettingsForm({ settings }: { settings: AccountSettings }) {
  const [result, setResult] = useState<string>("");

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    const payload = {
      marketing_emails_enabled: formData.get("marketing_emails_enabled") === "on",
      product_updates_enabled: formData.get("product_updates_enabled") === "on",
      push_notifications_enabled: formData.get("push_notifications_enabled") === "on",
      favorite_categories: String(formData.get("favorite_categories") || "")
        .split(",")
        .map((item) => item.trim())
        .filter(Boolean),
    };
    const updated = await accountApi.updateSettings(payload);
    setResult(JSON.stringify(updated, null, 2));
  }

  return (
    <form onSubmit={onSubmit} className="space-y-4 rounded-2xl border p-5">
      <h2 className="text-xl font-semibold">Communication settings</h2>
      <label className="flex items-center gap-3 text-sm">
        <input name="marketing_emails_enabled" type="checkbox" defaultChecked={settings.marketing_emails_enabled} />
        Marketing emails
      </label>
      <label className="flex items-center gap-3 text-sm">
        <input name="product_updates_enabled" type="checkbox" defaultChecked={settings.product_updates_enabled} />
        Product updates
      </label>
      <label className="flex items-center gap-3 text-sm">
        <input name="push_notifications_enabled" type="checkbox" defaultChecked={settings.push_notifications_enabled} />
        Push notifications
      </label>
      <input
        name="favorite_categories"
        defaultValue={settings.favorite_categories.join(", ")}
        className="w-full rounded-xl border px-3 py-2"
      />
      <button className="rounded-xl border px-4 py-2">Save settings</button>
      {result ? <pre className="overflow-auto rounded-xl bg-slate-50 p-3 text-xs">{result}</pre> : null}
    </form>
  );
}
