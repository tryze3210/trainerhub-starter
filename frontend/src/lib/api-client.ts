import { API_BASE_URL } from '@/lib/config';
import { clearTokens, getAccessToken, getRefreshToken, persistTokens } from '@/lib/auth';
import type { ApiErrorShape } from '@/types/api';

type ApiRequestOptions = RequestInit & {
  auth?: boolean;
  retryOnAuthError?: boolean;
};

export type PaginatedResponse<T> = {
  count?: number;
  next?: string | null;
  previous?: string | null;
  results: T[];
};

function isPaginatedResponse<T>(value: unknown): value is PaginatedResponse<T> {
  return Boolean(
    value &&
      typeof value === 'object' &&
      'results' in value &&
      Array.isArray((value as PaginatedResponse<T>).results)
  );
}

export function normalizeListResponse<T>(data: T[] | PaginatedResponse<T> | null | undefined): T[] {
  if (!data) return [];
  if (Array.isArray(data)) return data;
  if (isPaginatedResponse<T>(data)) return data.results;
  return [];
}

function getCookie(name: string): string {
  if (typeof document === 'undefined') return '';
  const cookies = document.cookie ? document.cookie.split('; ') : [];
  const prefix = `${encodeURIComponent(name)}=`;
  const match = cookies.find((cookie) => cookie.startsWith(prefix));
  return match ? decodeURIComponent(match.slice(prefix.length)) : '';
}

function isUnsafeMethod(method?: string): boolean {
  const normalized = (method || 'GET').toUpperCase();
  return !['GET', 'HEAD', 'OPTIONS', 'TRACE'].includes(normalized);
}

function applyCsrfHeader(headers: Headers, method?: string): void {
  if (!isUnsafeMethod(method) || headers.has('X-CSRFToken')) return;
  const csrfToken = getCookie('csrftoken');
  if (csrfToken) {
    headers.set('X-CSRFToken', csrfToken);
  }
}

export async function parseResponse<T>(response: Response): Promise<T> {
  if (response.status === 204) {
    return undefined as T;
  }

  const text = await response.text();
  if (!text) {
    return undefined as T;
  }

  return JSON.parse(text) as T;
}

async function refreshAccessToken(): Promise<boolean> {
  const refreshToken = getRefreshToken();
  const variants = [
    {},
    { refresh: refreshToken },
    { refresh_token: refreshToken },
  ];

  for (const body of variants) {
    const headers = new Headers({ 'Content-Type': 'application/json' });
    applyCsrfHeader(headers, 'POST');
    const response = await fetch(`${API_BASE_URL}/auth/refresh/`, {
      method: 'POST',
      headers,
      body: JSON.stringify(body),
      cache: 'no-store',
      credentials: 'include',
    });

    if (!response.ok) {
      continue;
    }

    const payload = await parseResponse<Record<string, unknown>>(response);
    const access = String(payload?.access_token || payload?.access || '');
    const refresh = String(payload?.refresh_token || payload?.refresh || refreshToken);

    if (access) {
      persistTokens(access, refresh);
    }
    return true;
  }

  clearTokens();
  return false;
}

function withPath(path: string): string {
  if (path.startsWith('http://') || path.startsWith('https://')) {
    return path;
  }
  return `${API_BASE_URL}${path}`;
}

export async function apiRequest<T>(path: string, options: ApiRequestOptions = {}): Promise<T> {
  const { auth = false, retryOnAuthError = true, headers, ...rest } = options;
  const requestHeaders = new Headers(headers || {});

  if (!requestHeaders.has('Content-Type') && !(rest.body instanceof FormData)) {
    requestHeaders.set('Content-Type', 'application/json');
  }
  applyCsrfHeader(requestHeaders, rest.method);

  if (auth) {
    const token = getAccessToken();
    if (token) {
      requestHeaders.set('Authorization', `Bearer ${token}`);
    }
  }

  const response = await fetch(withPath(path), {
    ...rest,
    headers: requestHeaders,
    cache: 'no-store',
    credentials: rest.credentials ?? 'include',
  });

  if (response.status === 401 && auth && retryOnAuthError) {
    const refreshed = await refreshAccessToken();
    if (refreshed) {
      return apiRequest<T>(path, {
        ...options,
        retryOnAuthError: false,
      });
    }
  }

  if (!response.ok) {
    let message = `HTTP ${response.status}`;

    try {
      const payload = await parseResponse<ApiErrorShape>(response);
      if (payload?.detail && typeof payload.detail === 'string') {
        message = payload.detail;
      } else if (payload && typeof payload === 'object') {
        const firstEntry = Object.entries(payload)[0];
        if (firstEntry) {
          const value = firstEntry[1];
          message = Array.isArray(value) ? String(value[0]) : String(value);
        }
      }
    } catch {
      // ignore parse errors for failed responses
    }

    throw new Error(message);
  }

  return parseResponse<T>(response);
}
