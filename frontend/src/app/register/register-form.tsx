"use client";

import { FormEvent, useState } from "react";
import { authApi } from "@/lib/api";

export function RegisterForm() {
  const [result, setResult] = useState<string>("");

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    const payload = {
      full_name: String(formData.get("full_name") || ""),
      email: String(formData.get("email") || ""),
      password: String(formData.get("password") || ""),
    };
    const account = await authApi.register(payload);
    setResult(JSON.stringify(account, null, 2));
  }

  return (
    <form onSubmit={onSubmit} className="space-y-4 rounded-2xl border p-5">
      <input name="full_name" placeholder="Full name" className="w-full rounded-xl border px-3 py-2" />
      <input name="email" type="email" placeholder="you@example.com" className="w-full rounded-xl border px-3 py-2" />
      <input name="password" type="password" placeholder="Password" className="w-full rounded-xl border px-3 py-2" />
      <button className="rounded-xl border px-4 py-2">Create account</button>
      {result ? <pre className="overflow-auto rounded-xl bg-slate-50 p-3 text-xs">{result}</pre> : null}
    </form>
  );
}
