import { apiFetch } from "./client";
import type { LoginResponse } from "@/types/auth";

export async function loginByEmail(email: string, password: string) {
  return apiFetch<LoginResponse>("/auth/login/", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export async function registerUser(payload: {
  email: string;
  password: string;
  first_name?: string;
  last_name?: string;
  role: "customer" | "trainer";
}) {
  return apiFetch("/auth/register/", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
