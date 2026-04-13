"use client";

import { useEffect, useState } from 'react';

import {
  fetchNotificationPreferences,
  fetchNotifications,
  markAllNotificationsRead,
  markNotificationRead,
  updateNotificationPreferences,
} from '../api';
import { NotificationPreferences, UserNotification } from '../types';

export function NotificationCenter() {
  const [notifications, setNotifications] = useState<UserNotification[]>([]);
  const [preferences, setPreferences] = useState<NotificationPreferences | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    async function load() {
      try {
        setLoading(true);
        const [items, prefs] = await Promise.all([fetchNotifications(50), fetchNotificationPreferences()]);
        if (!active) return;
        setNotifications(items);
        setPreferences(prefs);
      } catch (err) {
        if (!active) return;
        setError(err instanceof Error ? err.message : 'Failed to load notifications.');
      } finally {
        if (active) setLoading(false);
      }
    }

    load();
    return () => {
      active = false;
    };
  }, []);

  async function handleMarkRead(notificationUuid: string) {
    await markNotificationRead(notificationUuid);
    setNotifications((prev) => prev.map((item) => (item.notification_uuid === notificationUuid ? { ...item, is_read: true } : item)));
  }

  async function handleMarkAllRead() {
    await markAllNotificationsRead();
    setNotifications((prev) => prev.map((item) => ({ ...item, is_read: true })));
  }

  async function handlePreferenceToggle(key: keyof NotificationPreferences, value: boolean) {
    const next = await updateNotificationPreferences({ [key]: value });
    setPreferences(next);
  }

  if (loading) {
    return <div className="rounded-2xl border border-zinc-800 bg-zinc-950 p-6 text-zinc-200">Loading notifications...</div>;
  }

  if (error) {
    return <div className="rounded-2xl border border-red-900 bg-red-950/30 p-6 text-red-200">{error}</div>;
  }

  return (
    <div className="grid gap-6 lg:grid-cols-[1.4fr_0.8fr]">
      <section className="rounded-2xl border border-zinc-800 bg-zinc-950 p-6 text-zinc-100 shadow-2xl shadow-black/20">
        <div className="mb-4 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold">Notification center</h1>
            <p className="mt-1 text-sm text-zinc-400">Platform announcements, order updates and system messages.</p>
          </div>
          <button onClick={handleMarkAllRead} className="rounded-xl border border-zinc-700 px-4 py-2 text-sm hover:bg-zinc-900">
            Mark all read
          </button>
        </div>

        <div className="space-y-4">
          {notifications.map((item) => (
            <article
              key={item.notification_uuid}
              className={`rounded-2xl border p-4 ${item.is_read ? 'border-zinc-800 bg-zinc-900/40' : 'border-emerald-700/50 bg-emerald-950/20'}`}
            >
              <div className="flex items-start justify-between gap-4">
                <div>
                  <div className="text-xs uppercase tracking-[0.2em] text-zinc-400">{item.notification_type}</div>
                  <h2 className="mt-1 text-lg font-medium">{item.title}</h2>
                  <p className="mt-2 whitespace-pre-line text-sm text-zinc-300">{item.body}</p>
                  {item.cta_url ? (
                    <a className="mt-3 inline-flex text-sm font-medium text-emerald-300 hover:text-emerald-200" href={item.cta_url}>
                      {item.cta_label || 'Open'}
                    </a>
                  ) : null}
                </div>
                {!item.is_read ? (
                  <button onClick={() => handleMarkRead(item.notification_uuid)} className="rounded-xl border border-zinc-700 px-3 py-2 text-xs hover:bg-zinc-900">
                    Mark read
                  </button>
                ) : (
                  <span className="text-xs text-zinc-500">Read</span>
                )}
              </div>
            </article>
          ))}
          {!notifications.length ? <div className="rounded-2xl border border-zinc-800 p-6 text-zinc-400">No notifications yet.</div> : null}
        </div>
      </section>

      <aside className="rounded-2xl border border-zinc-800 bg-zinc-950 p-6 text-zinc-100 shadow-2xl shadow-black/20">
        <h2 className="text-lg font-semibold">Preferences</h2>
        <div className="mt-4 space-y-4">
          {preferences ? (
            <>
              {[
                ['in_app_enabled', 'In-app notifications'],
                ['email_enabled', 'Email notifications'],
                ['marketing_enabled', 'Marketing announcements'],
                ['product_updates_enabled', 'Product updates'],
              ].map(([key, label]) => (
                <label key={key} className="flex items-center justify-between rounded-xl border border-zinc-800 px-4 py-3">
                  <span className="text-sm text-zinc-300">{label}</span>
                  <input
                    type="checkbox"
                    checked={Boolean(preferences[key as keyof NotificationPreferences])}
                    onChange={(event) => handlePreferenceToggle(key as keyof NotificationPreferences, event.target.checked)}
                  />
                </label>
              ))}
            </>
          ) : null}
        </div>
      </aside>
    </div>
  );
}
