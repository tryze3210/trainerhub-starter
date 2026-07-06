import { clearTokens } from '@/lib/auth';
import { apiRequest } from '@/lib/api-client';
import type { AuthResponse, SessionPayload } from '@/types/api';
import { normalizeAuthResponse, normalizeSessionPayload, splitFullName } from './normalizers';

type RegisterPayload = {
  email: string;
  password: string;
  full_name?: string;
  first_name?: string;
  last_name?: string;
  role?: 'user' | 'trainer';
};

export const authApi = {
  async register(payload: RegisterPayload): Promise<AuthResponse> {
    const names = payload.full_name
      ? splitFullName(payload.full_name)
      : {
          first_name: payload.first_name || '',
          last_name: payload.last_name || '',
        };

    const registerPayload = {
      email: payload.email,
      password: payload.password,
      first_name: names.first_name,
      last_name: names.last_name,
      role: payload.role || 'user',
    };

    const registerResponse = await apiRequest<Record<string, unknown>>('/auth/register/', {
      method: 'POST',
      body: JSON.stringify(registerPayload),
    });

    if (registerResponse.access || registerResponse.access_token) {
      return normalizeAuthResponse(registerResponse);
    }

    const loginResponse = await apiRequest<Record<string, unknown>>('/auth/login/', {
      method: 'POST',
      body: JSON.stringify({
        email: payload.email,
        password: payload.password,
      }),
    });

    return normalizeAuthResponse(loginResponse);
  },

  async login(payload: { email: string; password: string }): Promise<AuthResponse> {
    const response = await apiRequest<Record<string, unknown>>('/auth/login/', {
      method: 'POST',
      body: JSON.stringify(payload),
    });

    return normalizeAuthResponse(response);
  },

  async me(): Promise<SessionPayload> {
    const response = await apiRequest<Record<string, unknown>>('/auth/me/', { auth: true });
    return normalizeSessionPayload(response);
  },

  async logout(): Promise<void> {
    clearTokens();
  },
};
