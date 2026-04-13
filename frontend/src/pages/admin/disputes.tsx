import React, { useEffect, useState } from 'react';
import { fetchAdminDisputeOverview, fetchAdminDisputeQueue } from '../../features/disputes/api';

export default function AdminDisputesPage() {
  const [overview, setOverview] = useState<any>(null);
  const [queue, setQueue] = useState<any[]>([]);

  useEffect(() => {
    const client = (window as any).apiClient;
    fetchAdminDisputeOverview(client).then(setOverview);
    fetchAdminDisputeQueue(client, {}).then((data) => setQueue(Array.isArray(data) ? data : data.results || []));
  }, []);

  return (
    <div style={{ padding: 24 }}>
      <h1>Dispute Center</h1>
      <pre>{JSON.stringify(overview, null, 2)}</pre>
      <h2>Queue</h2>
      <ul>
        {queue.map((item) => (
          <li key={item.id}>{item.public_id} — {item.dispute_type} — {item.status} — {item.subject}</li>
        ))}
      </ul>
    </div>
  );
}
