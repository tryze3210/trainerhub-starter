import { apiRequest, normalizeListResponse } from '@/lib/api-client';

export type NotificationItem = {
  id: string;
  db_id?: number;
  notification_type: string;
  channel: string;
  title: string;
  body: string;
  cta_label?: string;
  cta_url?: string;
  metadata?: Record<string, unknown>;
  status: string;
  is_read: boolean;
  read_at?: string | null;
  sent_at?: string | null;
  created_at: string;
  user_email?: string;
};

export type NotificationPreferences = {
  in_app_enabled: boolean;
  email_enabled: boolean;
  marketing_enabled: boolean;
  product_updates_enabled: boolean;
  quiet_hours_start?: string | null;
  quiet_hours_end?: string | null;
};

export type NotificationInbox = {
  summary: {
    total: number;
    unread: number;
    read: number;
    by_type: Record<string, number>;
  };
  preferences: NotificationPreferences;
  results: NotificationItem[];
};

export type AdminAnnouncement = {
  id: string;
  db_id?: number;
  title: string;
  body: string;
  cta_label?: string;
  cta_url?: string;
  audience_type: string;
  is_published: boolean;
  starts_at?: string | null;
  ends_at?: string | null;
  published_at?: string | null;
  created_at: string;
  created_by?: string;
  created_by_email?: string;
  notifications_count?: number | null;
  created_notifications?: number;
};

export type AdminNotificationCenter = {
  period: { days: number; since: string; generated_at: string };
  summary: {
    notifications_total: number;
    notifications_unread: number;
    notifications_read: number;
    deliveries_total: number;
    deliveries_pending: number;
    deliveries_sent: number;
    deliveries_failed: number;
    announcements_total: number;
    announcements_published: number;
    announcements_draft: number;
  };
  channels: Array<{ channel: string; count: number; unread: number }>;
  types: Array<{ notification_type: string; count: number; unread: number }>;
  recent_announcements: AdminAnnouncement[];
  recent_failed_deliveries: Array<Record<string, string | number | null>>;
  recent_notifications: NotificationItem[];
  health: {
    status: string;
    checks: Array<{ code: string; title: string; status: string; value: number }>;
  };
};

export const notificationsApi = {
  getInbox: (params?: { unread?: boolean; limit?: number }) => {
    const search = new URLSearchParams();
    if (params?.unread) search.set('unread', 'true');
    if (params?.limit) search.set('limit', String(params.limit));
    const query = search.toString();
    return apiRequest<NotificationInbox>(`/notifications/inbox/${query ? `?${query}` : ''}`, { auth: true });
  },
  markRead: (notificationId: string) =>
    apiRequest<NotificationItem>(`/notifications/inbox/${notificationId}/read/`, { auth: true, method: 'POST' }),
  markAllRead: () => apiRequest<{ updated: number }>('/notifications/inbox/mark-all-read/', { auth: true, method: 'POST' }),
  getPreferences: () => apiRequest<NotificationPreferences>('/notifications/preferences/', { auth: true }),
  updatePreferences: (payload: Partial<NotificationPreferences>) =>
    apiRequest<NotificationPreferences>('/notifications/preferences/', {
      auth: true,
      method: 'PATCH',
      body: JSON.stringify(payload),
    }),
  getAdminCenter: (days = 30) => apiRequest<AdminNotificationCenter>(`/notifications/admin/center/?days=${days}`, { auth: true }),
  listAnnouncements: () =>
    apiRequest<AdminAnnouncement[] | { results: AdminAnnouncement[] }>('/notifications/admin/announcements/', { auth: true }).then(normalizeListResponse),
  createAnnouncement: (payload: {
    title: string;
    body: string;
    audience_type: 'all_users' | 'all_trainers' | 'specific_users';
    cta_label?: string;
    cta_url?: string;
    publish_now?: boolean;
    user_ids?: string[];
  }) =>
    apiRequest<AdminAnnouncement>('/notifications/admin/announcements/', {
      auth: true,
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  publishAnnouncement: (announcementId: string) =>
    apiRequest<AdminAnnouncement>(`/notifications/admin/announcements/${announcementId}/publish/`, {
      auth: true,
      method: 'POST',
    }),
};
