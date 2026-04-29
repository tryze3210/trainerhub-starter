import type { AuthResponse, AuthUser, SessionPayload } from '@/types/api';

function normalizeRole(value: unknown): string {
  if (value === 'customer') {
    return 'user';
  }
  return typeof value === 'string' && value ? value : 'user';
}

export function splitFullName(fullName: string): { first_name: string; last_name: string } {
  const normalized = fullName.trim().replace(/\s+/g, ' ');
  if (!normalized) {
    return { first_name: '', last_name: '' };
  }

  const parts = normalized.split(' ');
  const first_name = parts.shift() || '';
  const last_name = parts.join(' ');
  return { first_name, last_name };
}

export function normalizeAuthUser(payload: Record<string, unknown> | null | undefined): AuthUser | null {
  if (!payload || typeof payload !== 'object') {
    return null;
  }

  const firstName = typeof payload.first_name === 'string' ? payload.first_name : '';
  const lastName = typeof payload.last_name === 'string' ? payload.last_name : '';
  const fullName = [firstName, lastName].filter(Boolean).join(' ').trim();
  const activeRole = normalizeRole(payload.active_role || payload.role);
  const availableRoles = Array.isArray(payload.available_roles)
    ? payload.available_roles
        .filter((item): item is string => typeof item === 'string' && Boolean(item))
        .map((item) => normalizeRole(item))
    : [activeRole];

  return {
    id: String(payload.id || ''),
    email: typeof payload.email === 'string' ? payload.email : '',
    full_name: typeof payload.full_name === 'string' && payload.full_name ? payload.full_name : fullName,
    display_name: typeof payload.display_name === 'string' ? payload.display_name : undefined,
    phone: typeof payload.phone === 'string' ? payload.phone : undefined,
    country: typeof payload.country === 'string' ? payload.country : undefined,
    city: typeof payload.city === 'string' ? payload.city : undefined,
    timezone: typeof payload.timezone === 'string' ? payload.timezone : undefined,
    preferred_language: typeof payload.preferred_language === 'string' ? payload.preferred_language : undefined,
    active_role: activeRole,
    available_roles: availableRoles.length ? availableRoles : [activeRole],
    settings: typeof payload.settings === 'object' && payload.settings ? (payload.settings as AuthUser['settings']) : undefined,
  };
}

export function normalizeSessionPayload(payload: unknown): SessionPayload {
  if (payload && typeof payload === 'object' && 'user' in payload) {
    const session = payload as Record<string, unknown>;
    return {
      is_authenticated: Boolean(session.is_authenticated ?? session.user),
      user: normalizeAuthUser(session.user as Record<string, unknown> | null | undefined),
    };
  }

  const user = normalizeAuthUser(payload as Record<string, unknown> | null | undefined);
  return {
    is_authenticated: Boolean(user),
    user,
  };
}

export function normalizeAuthResponse(payload: Record<string, unknown>): AuthResponse {
  const user = normalizeAuthUser(
    (payload.user as Record<string, unknown> | undefined) || payload
  );

  return {
    user: user || {
      id: '',
      email: '',
      full_name: '',
      active_role: 'user',
      available_roles: ['user'],
    },
    access_token: String(payload.access_token || payload.access || ''),
    refresh_token: String(payload.refresh_token || payload.refresh || ''),
  };
}
