'use client';

import { useEffect, useState } from 'react';
import { getNotificationDeliveryOverview, getNotificationDeliveries, getNotificationTemplates } from '@/features/notifications/admin-api';

export default function AdminNotificationTemplatesPage() {
  const [overview, setOverview] = useState<any>(null);
  const [templates, setTemplates] = useState<any[]>([]);
  const [deliveries, setDeliveries] = useState<any[]>([]);

  useEffect(() => {
    getNotificationDeliveryOverview().then(setOverview);
    getNotificationTemplates().then((data) => setTemplates(data.results ?? data));
    getNotificationDeliveries().then((data) => setDeliveries(data.results ?? data));
  }, []);

  return (
    <div className="space-y-6 p-6">
      <h1 className="text-2xl font-semibold">Notification Templates & Delivery</h1>

      <section className="grid gap-4 md:grid-cols-3 xl:grid-cols-6">
        {overview && Object.entries(overview).map(([key, value]) => (
          <div key={key} className="rounded-2xl border p-4 shadow-sm">
            <div className="text-sm text-neutral-500">{key}</div>
            <div className="mt-2 text-2xl font-semibold">{String(value)}</div>
          </div>
        ))}
      </section>

      <section className="rounded-2xl border p-4 shadow-sm">
        <h2 className="mb-4 text-lg font-medium">Templates</h2>
        <div className="space-y-3">
          {templates.map((item) => (
            <div key={item.id} className="rounded-xl border p-3">
              <div className="font-medium">{item.code}</div>
              <div className="text-sm text-neutral-500">{item.channel}</div>
              <div className="mt-2 text-sm">{item.subject_template}</div>
            </div>
          ))}
        </div>
      </section>

      <section className="rounded-2xl border p-4 shadow-sm">
        <h2 className="mb-4 text-lg font-medium">Recent Deliveries</h2>
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead>
              <tr className="text-left text-neutral-500">
                <th className="pb-2 pr-4">Type</th>
                <th className="pb-2 pr-4">Channel</th>
                <th className="pb-2 pr-4">Status</th>
                <th className="pb-2 pr-4">Subject</th>
                <th className="pb-2 pr-4">Sent at</th>
              </tr>
            </thead>
            <tbody>
              {deliveries.map((item) => (
                <tr key={item.id} className="border-t align-top">
                  <td className="py-2 pr-4">{item.type}</td>
                  <td className="py-2 pr-4">{item.channel}</td>
                  <td className="py-2 pr-4">{item.status}</td>
                  <td className="py-2 pr-4">{item.subject}</td>
                  <td className="py-2 pr-4">{item.sent_at ?? '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
