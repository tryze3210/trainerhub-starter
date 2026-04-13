"use client";

import { FormEvent, useEffect, useState } from 'react';

import { createAdminAnnouncement, fetchAdminAnnouncements, fetchAdminNotificationOverview, fetchDeliveryBreakdown } from '@/features/notifications/api';
import { AdminAnnouncement, AdminNotificationOverview, DeliveryBreakdownRow } from '@/features/notifications/types';

const initialForm = {
  title: '',
  body: '',
  cta_label: '',
  cta_url: '',
  audience_type: 'all_users',
  starts_at: new Date().toISOString().slice(0, 16),
};

export function AdminAnnouncementsDashboard() {
  const [overview, setOverview] = useState<AdminNotificationOverview | null>(null);
  const [announcements, setAnnouncements] = useState<AdminAnnouncement[]>([]);
  const [breakdown, setBreakdown] = useState<DeliveryBreakdownRow[]>([]);
  const [form, setForm] = useState(initialForm);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    try {
      setError(null);
      const [overviewData, announcementsData, breakdownData] = await Promise.all([
        fetchAdminNotificationOverview(),
        fetchAdminAnnouncements(),
        fetchDeliveryBreakdown(),
      ]);
      setOverview(overviewData);
      setAnnouncements(announcementsData);
      setBreakdown(breakdownData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load admin notifications.');
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await createAdminAnnouncement({ ...form, starts_at: new Date(form.starts_at).toISOString() });
    setForm(initialForm);
    await load();
  }

  return (
    <div className="space-y-6 text-zinc-100">
      {error ? <div className="rounded-2xl border border-red-900 bg-red-950/30 p-4 text-red-200">{error}</div> : null}

      <section className="grid gap-4 md:grid-cols-5">
        {overview
          ? [
              ['Published', overview.published_announcements],
              ['Active', overview.active_announcements],
              ['Total notifications', overview.total_notifications],
              ['Unread', overview.unread_notifications],
              ['Failed', overview.failed_notifications],
            ].map(([label, value]) => (
              <div key={String(label)} className="rounded-2xl border border-zinc-800 bg-zinc-950 p-5 shadow-2xl shadow-black/20">
                <div className="text-sm text-zinc-400">{label}</div>
                <div className="mt-2 text-3xl font-semibold">{value}</div>
              </div>
            ))
          : null}
      </section>

      <section className="grid gap-6 lg:grid-cols-[1fr_1fr]">
        <form onSubmit={handleSubmit} className="rounded-2xl border border-zinc-800 bg-zinc-950 p-6 shadow-2xl shadow-black/20">
          <h1 className="text-2xl font-semibold">Publish announcement</h1>
          <div className="mt-4 grid gap-4">
            <input className="rounded-xl border border-zinc-800 bg-zinc-900 px-4 py-3" placeholder="Title" value={form.title} onChange={(e) => setForm((prev) => ({ ...prev, title: e.target.value }))} />
            <textarea className="min-h-40 rounded-xl border border-zinc-800 bg-zinc-900 px-4 py-3" placeholder="Body" value={form.body} onChange={(e) => setForm((prev) => ({ ...prev, body: e.target.value }))} />
            <div className="grid gap-4 md:grid-cols-2">
              <input className="rounded-xl border border-zinc-800 bg-zinc-900 px-4 py-3" placeholder="CTA label" value={form.cta_label} onChange={(e) => setForm((prev) => ({ ...prev, cta_label: e.target.value }))} />
              <input className="rounded-xl border border-zinc-800 bg-zinc-900 px-4 py-3" placeholder="CTA URL" value={form.cta_url} onChange={(e) => setForm((prev) => ({ ...prev, cta_url: e.target.value }))} />
            </div>
            <div className="grid gap-4 md:grid-cols-2">
              <select className="rounded-xl border border-zinc-800 bg-zinc-900 px-4 py-3" value={form.audience_type} onChange={(e) => setForm((prev) => ({ ...prev, audience_type: e.target.value }))}>
                <option value="all_users">All users</option>
                <option value="all_trainers">All trainers</option>
                <option value="specific_users">Specific users</option>
              </select>
              <input type="datetime-local" className="rounded-xl border border-zinc-800 bg-zinc-900 px-4 py-3" value={form.starts_at} onChange={(e) => setForm((prev) => ({ ...prev, starts_at: e.target.value }))} />
            </div>
            <button className="rounded-xl bg-emerald-500 px-4 py-3 font-semibold text-black hover:bg-emerald-400">Create and publish</button>
          </div>
        </form>

        <div className="rounded-2xl border border-zinc-800 bg-zinc-950 p-6 shadow-2xl shadow-black/20">
          <h2 className="text-xl font-semibold">Delivery breakdown</h2>
          <div className="mt-4 overflow-hidden rounded-xl border border-zinc-800">
            <table className="min-w-full divide-y divide-zinc-800 text-sm">
              <thead className="bg-zinc-900 text-zinc-400">
                <tr>
                  <th className="px-4 py-3 text-left">Type</th>
                  <th className="px-4 py-3 text-left">Status</th>
                  <th className="px-4 py-3 text-right">Count</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-800">
                {breakdown.map((row) => (
                  <tr key={`${row.notification_type}-${row.status}`}>
                    <td className="px-4 py-3">{row.notification_type}</td>
                    <td className="px-4 py-3">{row.status}</td>
                    <td className="px-4 py-3 text-right">{row.total}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <section className="rounded-2xl border border-zinc-800 bg-zinc-950 p-6 shadow-2xl shadow-black/20">
        <h2 className="text-xl font-semibold">Recent announcements</h2>
        <div className="mt-4 space-y-4">
          {announcements.map((item) => (
            <article key={item.announcement_uuid} className="rounded-2xl border border-zinc-800 bg-zinc-900/40 p-4">
              <div className="flex items-center justify-between gap-4">
                <div>
                  <div className="text-xs uppercase tracking-[0.2em] text-zinc-500">{item.audience_type}</div>
                  <h3 className="mt-1 text-lg font-medium">{item.title}</h3>
                  <p className="mt-2 whitespace-pre-line text-sm text-zinc-300">{item.body}</p>
                </div>
                <div className="text-right text-xs text-zinc-500">
                  <div>{item.is_published ? 'Published' : 'Draft'}</div>
                  <div className="mt-2">{new Date(item.created_at).toLocaleString()}</div>
                </div>
              </div>
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}
