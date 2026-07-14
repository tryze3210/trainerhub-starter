import { apiRequest, normalizeListResponse } from '@/lib/api-client';
import { getAccessToken } from '@/lib/auth';
import { API_BASE_URL } from '@/lib/config';

export type ReferralMoney = string | number | null | undefined;

export type ReferralAdminListParams = {
  status?: string;
  program_slug?: string;
  owner_id?: string;
  referred_user_id?: string;
  created_from?: string;
  created_to?: string;
  search?: string;
};

export type ReferralAdminExportKind = 'rewards' | 'ledger' | 'invites';

export type ReferralAdminMetricBucket = {
  status?: string;
  entry_type?: string;
  program_slug?: string;
  count?: number;
  amount?: ReferralMoney;
  reward_amount?: ReferralMoney;
  currency?: string;
};

export type ReferralAdminIntegritySnapshot = {
  issue_count?: number;
  stale_pending_invites?: number;
  converted_invites_without_attribution?: number;
  approved_rewards_without_ledger?: number;
  rewards_with_multiple_ledger_entries?: number;
  reward_ledger_entries_without_reward?: number;
  [key: string]: unknown;
};

export type ReferralAdminOpsOverview = {
  days?: number;
  window_days?: number;
  generated_at?: string;
  totals?: Record<string, string | number | null | undefined>;
  rewards_by_status?: ReferralAdminMetricBucket[];
  ledger_by_type?: ReferralAdminMetricBucket[];
  programs?: ReferralAdminMetricBucket[];
  integrity?: ReferralAdminIntegritySnapshot;
};

export type ReferralAdminReward = {
  id: string;
  attribution?: string | null;
  attribution_id?: string | null;
  program_slug?: string | null;
  owner_id?: string | null;
  owner_email?: string | null;
  referred_user_id?: string | null;
  referred_email?: string | null;
  status?: string | null;
  reward_kind?: string | null;
  reward_amount?: ReferralMoney;
  amount?: ReferralMoney;
  currency?: string | null;
  trigger_type?: string | null;
  trigger_reference?: string | null;
  approved_at?: string | null;
  created_at?: string | null;
  metadata?: Record<string, unknown> | null;
};

export type ReferralAdminLedgerEntry = {
  id: string;
  reward?: string | null;
  reward_id?: string | null;
  entry_type?: string | null;
  amount?: ReferralMoney;
  currency?: string | null;
  reason?: string | null;
  created_at?: string | null;
  metadata?: Record<string, unknown> | null;
};

export type ReferralAdminInvite = {
  id: string;
  code?: string | null;
  referral_code?: string | null;
  program_slug?: string | null;
  owner_id?: string | null;
  landing_path?: string | null;
  click_session_key?: string | null;
  status?: string | null;
  created_at?: string | null;
  converted_at?: string | null;
};

export type ReferralAdminAttribution = {
  id: string;
  invite?: string | null;
  invite_id?: string | null;
  code?: string | null;
  referral_code?: string | null;
  program_slug?: string | null;
  owner_id?: string | null;
  referred_user_id?: string | null;
  status?: string | null;
  source?: string | null;
  created_at?: string | null;
  converted_at?: string | null;
};

function buildQuery(params?: ReferralAdminListParams & { days?: number }): string {
  const search = new URLSearchParams();

  Object.entries(params || {}).forEach(([key, value]) => {
    if (value === undefined || value === null || value === '') return;
    search.set(key, String(value));
  });

  const query = search.toString();
  return query ? `?${query}` : '';
}


function withApiBase(path: string): string {
  if (path.startsWith('http://') || path.startsWith('https://')) {
    return path;
  }

  return `${API_BASE_URL}${path}`;
}

function filenameFromContentDisposition(value: string | null, fallback: string): string {
  if (!value) return fallback;

  const utf8Match = value.match(/filename\*=UTF-8''([^;]+)/i);
  if (utf8Match?.[1]) {
    try {
      return decodeURIComponent(utf8Match[1].replace(/"/g, '').trim());
    } catch {
      return utf8Match[1].replace(/"/g, '').trim() || fallback;
    }
  }

  const asciiMatch = value.match(/filename="?([^";]+)"?/i);
  return asciiMatch?.[1]?.trim() || fallback;
}

function defaultExportFilename(kind: ReferralAdminExportKind): string {
  const date = new Date().toISOString().slice(0, 10);
  return `trainerhub-referrals-${kind}-${date}.csv`;
}

export function buildReferralAdminExportPath(
  kind: ReferralAdminExportKind,
  params?: ReferralAdminListParams
): string {
  return `/referrals/admin/${kind}/export.csv${buildQuery(params)}`;
}

export async function downloadReferralAdminCsv(
  kind: ReferralAdminExportKind,
  params?: ReferralAdminListParams
): Promise<string> {
  if (typeof window === 'undefined' || typeof document === 'undefined') {
    throw new Error('CSV export is available only in browser session');
  }

  const token = getAccessToken();
  const response = await fetch(withApiBase(buildReferralAdminExportPath(kind, params)), {
    method: 'GET',
    headers: token ? { Authorization: `Bearer ${token}` } : undefined,
    cache: 'no-store',
    credentials: 'include',
  });

  if (!response.ok) {
    const message = await response.text().catch(() => '');
    throw new Error(message || `CSV export failed: HTTP ${response.status}`);
  }

  const blob = await response.blob();
  const filename = filenameFromContentDisposition(
    response.headers.get('Content-Disposition'),
    defaultExportFilename(kind)
  );

  const url = window.URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename;
  anchor.rel = 'noopener';
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  window.URL.revokeObjectURL(url);

  return filename;
}

export const referralsAdminApi = {
  getOpsOverview(days = 30): Promise<ReferralAdminOpsOverview> {
    return apiRequest(`/referrals/admin/ops/overview/${buildQuery({ days })}`, { auth: true });
  },

  async listRewards(params?: ReferralAdminListParams): Promise<ReferralAdminReward[]> {
    const payload = await apiRequest<ReferralAdminReward[] | { results: ReferralAdminReward[] }>(
      `/referrals/admin/rewards/${buildQuery(params)}`,
      { auth: true }
    );
    return normalizeListResponse(payload);
  },

  getReward(id: string): Promise<ReferralAdminReward> {
    return apiRequest(`/referrals/admin/rewards/${id}/`, { auth: true });
  },

  async listLedger(params?: ReferralAdminListParams): Promise<ReferralAdminLedgerEntry[]> {
    const payload = await apiRequest<ReferralAdminLedgerEntry[] | { results: ReferralAdminLedgerEntry[] }>(
      `/referrals/admin/ledger/${buildQuery(params)}`,
      { auth: true }
    );
    return normalizeListResponse(payload);
  },

  async listInvites(params?: ReferralAdminListParams): Promise<ReferralAdminInvite[]> {
    const payload = await apiRequest<ReferralAdminInvite[] | { results: ReferralAdminInvite[] }>(
      `/referrals/admin/invites/${buildQuery(params)}`,
      { auth: true }
    );
    return normalizeListResponse(payload);
  },

  getInvite(id: string): Promise<ReferralAdminInvite> {
    return apiRequest(`/referrals/admin/invites/${id}/`, { auth: true });
  },

  async listAttributions(params?: ReferralAdminListParams): Promise<ReferralAdminAttribution[]> {
    const payload = await apiRequest<ReferralAdminAttribution[] | { results: ReferralAdminAttribution[] }>(
      `/referrals/admin/attributions/${buildQuery(params)}`,
      { auth: true }
    );
    return normalizeListResponse(payload);
  },
};
