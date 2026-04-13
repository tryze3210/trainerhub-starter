"use client";

import { FormEvent, useState } from "react";
import { authApi } from "@/lib/api";

export function LoginForm() {
  const [result, setResult] = useState<string>("");

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    const payload = {
      email: String(formData.get("email") || ""),
      password: String(formData.get("password") || ""),
    };
    const session = await authApi.login(payload);
    setResult(JSON.stringify(session, null, 2));
  }

  return (
    <form onSubmit={onSubmit} className="space-y-4 rounded-2xl border p-5">
      <input name="email" type="email" defaultValue="member@trainerhub.local" className="w-full rounded-xl border px-3 py-2" />
      <input name="password" type="password" defaultValue="demo-password" className="w-full rounded-xl border px-3 py-2" />
      <button className="rounded-xl border px-4 py-2">Login</button>
      {result ? <pre className="overflow-auto rounded-xl bg-slate-50 p-3 text-xs">{result}</pre> : null}
    </form>
  );
}
