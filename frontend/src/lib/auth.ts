const ACCESS_TOKEN_KEY = 'trainerhub.access_token';
const REFRESH_TOKEN_KEY = 'trainerhub.refresh_token';

function hasWindow() {
  return typeof window !== 'undefined';
}

export function getAccessToken(): string | null {
  return null;
}

export function getRefreshToken(): string | null {
  return null;
}

export function hasTokens(): boolean {
  return hasWindow();
}

export function persistTokens(accessToken: string, refreshToken: string) {
  if (!hasWindow()) return;
  void accessToken;
  void refreshToken;
  clearTokens();
}

export function clearTokens() {
  if (!hasWindow()) return;
  window.localStorage.removeItem(ACCESS_TOKEN_KEY);
  window.localStorage.removeItem(REFRESH_TOKEN_KEY);
}
