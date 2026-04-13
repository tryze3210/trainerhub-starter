import React, { useEffect, useState } from 'react';
import { fetchMyGamificationDashboard, fetchMyLeaderboard } from '../features/gamification/api';

export default function TrainerGamificationPage() {
  const [dashboard, setDashboard] = useState<any>(null);
  const [leaderboard, setLeaderboard] = useState<any[]>([]);

  useEffect(() => {
    const client = (window as any).apiClient;
    if (!client) return;
    fetchMyGamificationDashboard(client).then(setDashboard);
    fetchMyLeaderboard(client).then(setLeaderboard);
  }, []);

  return (
    <div style={{ padding: 24 }}>
      <h1>Gamification</h1>
      <pre>{JSON.stringify(dashboard, null, 2)}</pre>
      <h2>Weekly leaderboard</h2>
      <pre>{JSON.stringify(leaderboard, null, 2)}</pre>
    </div>
  );
}
