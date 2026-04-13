"use client";

import { FormEvent, useState } from "react";
import { AccountProfile, accountApi } from "@/lib/api";

export function ProfileForm({ profile }: { profile: AccountProfile }) {
  const [result, setResult] = useState<string>("");

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    const payload = {
      full_name: String(formData.get("full_name") || ""),
      display_name: String(formData.get("display_name") || ""),
      phone: String(formData.get("phone") || ""),
      country: String(formData.get("country") || ""),
      city: String(formData.get("city") || ""),
      timezone: String(formData.get("timezone") || ""),
      preferred_language: String(formData.get("preferred_language") || ""),
    };
    const updated = await accountApi.updateProfile(payload);
    setResult(JSON.stringify(updated, null, 2));
  }

  return (
    <form onSubmit={onSubmit} className="space-y-4 rounded-2xl border p-5">
      <h2 className="text-xl font-semibold">Profile</h2>
      <input name="full_name" defaultValue={profile.full_name} className="w-full rounded-xl border px-3 py-2" />
      <input name="display_name" defaultValue={profile.display_name} className="w-full rounded-xl border px-3 py-2" />
      <input name="phone" defaultValue={profile.phone} className="w-full rounded-xl border px-3 py-2" />
      <input name="country" defaultValue={profile.country} className="w-full rounded-xl border px-3 py-2" />
      <input name="city" defaultValue={profile.city} className="w-full rounded-xl border px-3 py-2" />
      <input name="timezone" defaultValue={profile.timezone} className="w-full rounded-xl border px-3 py-2" />
      <input name="preferred_language" defaultValue={profile.preferred_language} className="w-full rounded-xl border px-3 py-2" />
      <button className="rounded-xl border px-4 py-2">Save profile</button>
      {result ? <pre className="overflow-auto rounded-xl bg-slate-50 p-3 text-xs">{result}</pre> : null}
    </form>
  );
}
