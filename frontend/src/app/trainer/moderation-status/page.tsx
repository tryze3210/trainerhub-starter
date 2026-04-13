'use client';

import { useEffect, useState } from 'react';
import { moderationApi } from '@/features/moderation/api';

export default function TrainerModerationStatusPage() {
  const [data, setData] = useState<any>({ cases: [], risk_flags: [] });

  useEffect(() => {
    moderationApi.getMyStatus().then(setData);
  }, []);

  return (
    <div className="space-y-6 p-6">
      <h1 className="text-2xl font-semibold">Moderation status</h1>
      <section className="rounded-2xl border p-4">
        <h2 className="mb-3 text-lg font-medium">My cases</h2>
        <div className="space-y-3">
          {data.cases.map((item: any) => (
            <div key={item.id} className="rounded-xl border p-3">
              <div className="font-medium">{item.title}</div>
              <div className="text-sm opacity-70">{item.status} · decision: {item.latest_decision || '—'}</div>
            </div>
          ))}
        </div>
      </section>
      <section className="rounded-2xl border p-4">
        <h2 className="mb-3 text-lg font-medium">Active risk flags</h2>
        <div className="space-y-3">
          {data.risk_flags.map((item: any) => (
            <div key={item.id} className="rounded-xl border p-3">
              <div className="font-medium">{item.label}</div>
              <div className="text-sm opacity-70">{item.code} · {item.risk_level}</div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
