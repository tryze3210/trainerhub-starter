export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost/api/v1";

export async function apiFetch<T>(path: string, init: RequestInit = {}, accessToken?: string | null): Promise<T> {
  const headers = new Headers(init.headers || {});
  if (!(init.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }
  if (accessToken) {
    headers.set("Authorization", `Bearer ${accessToken}`);
  }
  const response = await fetch(`${API_BASE_URL}${path}`, { ...init, headers, credentials: "include" });
  if (!response.ok) {
    throw await response.json().catch(() => ({ message: "Request failed" }));
  }
  return response.json() as Promise<T>;
}
