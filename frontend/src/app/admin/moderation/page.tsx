'use client';

import { useEffect, useState } from 'react';
import { moderationApi } from '@/features/moderation/api';

export default function AdminModerationPage() {
  const [overview, setOverview] = useState<any>(null);
  const [queue, setQueue] = useState<any[]>([]);

  useEffect(() => {
    moderationApi.getOverview().then(setOverview);
    moderationApi.getQueue().then(setQueue);
  }, []);

  return (
    <div className="space-y-6 p-6">
      <h1 className="text-2xl font-semibold">Moderation</h1>
      <div className="grid grid-cols-2 gap-4 md:grid-cols-5">
        <Stat label="Open" value={overview?.totals?.open ?? 0} />
        <Stat label="In review" value={overview?.totals?.in_review ?? 0} />
        <Stat label="Escalated" value={overview?.totals?.escalated ?? 0} />
        <Stat label="Resolved" value={overview?.totals?.resolved ?? 0} />
        <Stat label="Risk flags" value={overview?.active_risk_flags ?? 0} />
      </div>
      <div className="rounded-2xl border p-4">
        <h2 className="mb-3 text-lg font-medium">Queue</h2>
        <div className="space-y-3">
          {queue.map((item) => (
            <div key={item.id} className="rounded-xl border p-3">
              <div className="font-medium">{item.title}</div>
              <div className="text-sm opacity-70">{item.target_type} · {item.status} · priority {item.priority}</div>
              <div className="mt-1 text-sm">{item.summary}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-2xl border p-4">
      <div className="text-sm opacity-70">{label}</div>
      <div className="text-2xl font-semibold">{value}</div>
    </div>
  );
}
