export type UserNotification = {
  notification_uuid: string;
  notification_type: string;
  channel: string;
  title: string;
  body: string;
  cta_label: string;
  cta_url: string;
  metadata: Record<string, unknown>;
  status: string;
  is_read: boolean;
  read_at: string | null;
  created_at: string;
};

export type NotificationPreferences = {
  in_app_enabled: boolean;
  email_enabled: boolean;
  marketing_enabled: boolean;
  product_updates_enabled: boolean;
  quiet_hours_start: string | null;
  quiet_hours_end: string | null;
};

export type NotificationCounter = {
  unread_count: number;
};

export type AdminNotificationOverview = {
  published_announcements: number;
  active_announcements: number;
  total_notifications: number;
  unread_notifications: number;
  failed_notifications: number;
};

export type AdminAnnouncement = {
  announcement_uuid: string;
  title: string;
  body: string;
  cta_label: string;
  cta_url: string;
  audience_type: string;
  starts_at: string;
  ends_at: string | null;
  is_published: boolean;
  published_at: string | null;
  created_at: string;
};

export type DeliveryBreakdownRow = {
  notification_type: string;
  status: string;
  total: number;
};
