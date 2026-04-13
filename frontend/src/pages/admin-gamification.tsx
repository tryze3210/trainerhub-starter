import React, { useEffect, useState } from 'react';
import { fetchAdminGamificationOverview, rebuildLeaderboards } from '../features/gamification/api';

export default function AdminGamificationPage() {
  const [overview, setOverview] = useState<any>(null);

  useEffect(() => {
    const client = (window as any).apiClient;
    if (!client) return;
    fetchAdminGamificationOverview(client).then(setOverview);
  }, []);

  const onRebuild = async () => {
    const client = (window as any).apiClient;
    if (!client) return;
    await rebuildLeaderboards(client, 'weekly');
    setOverview(await fetchAdminGamificationOverview(client));
  };

  return (
    <div style={{ padding: 24 }}>
      <h1>Admin Gamification</h1>
      <button onClick={onRebuild}>Rebuild weekly leaderboard</button>
      <pre>{JSON.stringify(overview, null, 2)}</pre>
    </div>
  );
}
