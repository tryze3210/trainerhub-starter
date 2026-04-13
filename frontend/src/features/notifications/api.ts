import {
  AdminAnnouncement,
  AdminNotificationOverview,
  DeliveryBreakdownRow,
  NotificationCounter,
  NotificationPreferences,
  UserNotification,
} from './types';

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers || {}),
    },
    cache: 'no-store',
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed: ${response.status}`);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

export function fetchNotifications(limit = 30) {
  return request<UserNotification[]>(`/api/v1/notifications/me/?limit=${limit}`);
}

export function fetchUnreadCount() {
  return request<NotificationCounter>('/api/v1/notifications/me/unread-count/');
}

export function markNotificationRead(notificationUuid: string) {
  return request<{ status: string }>(`/api/v1/notifications/me/${notificationUuid}/mark-read/`, { method: 'POST' });
}

export function markAllNotificationsRead() {
  return request<{ marked_read: number }>('/api/v1/notifications/me/mark-all-read/', { method: 'POST' });
}

export function fetchNotificationPreferences() {
  return request<NotificationPreferences>('/api/v1/notifications/me/preferences/');
}

export function updateNotificationPreferences(payload: Partial<NotificationPreferences>) {
  return request<NotificationPreferences>('/api/v1/notifications/me/preferences/', { method: 'PATCH', body: JSON.stringify(payload) });
}

export function fetchAdminNotificationOverview() {
  return request<AdminNotificationOverview>('/api/v1/notifications/admin/overview/');
}

export function fetchAdminAnnouncements() {
  return request<AdminAnnouncement[]>('/api/v1/notifications/admin/announcements/');
}

export function createAdminAnnouncement(payload: Record<string, unknown>) {
  return request<AdminAnnouncement>('/api/v1/notifications/admin/announcements/create/?publish=true', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export function fetchDeliveryBreakdown() {
  return request<DeliveryBreakdownRow[]>('/api/v1/notifications/admin/delivery-breakdown/');
}
