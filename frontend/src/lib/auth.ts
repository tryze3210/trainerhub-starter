'use client';

const ACCESS_TOKEN_KEY = 'trainerhub.access_token';
const REFRESH_TOKEN_KEY = 'trainerhub.refresh_token';

function hasWindow() {
  return typeof window !== 'undefined';
}

export function getAccessToken(): string | null {
  return hasWindow() ? window.localStorage.getItem(ACCESS_TOKEN_KEY) : null;
}

export function getRefreshToken(): string | null {
  return hasWindow() ? window.localStorage.getItem(REFRESH_TOKEN_KEY) : null;
}

export function hasTokens(): boolean {
  return Boolean(getAccessToken() && getRefreshToken());
}

export function persistTokens(accessToken: string, refreshToken: string) {
  if (!hasWindow()) return;
  window.localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
  window.localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
}

export function clearTokens() {
  if (!hasWindow()) return;
  window.localStorage.removeItem(ACCESS_TOKEN_KEY);
  window.localStorage.removeItem(REFRESH_TOKEN_KEY);
}
