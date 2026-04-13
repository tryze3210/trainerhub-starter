export async function fetchMyGamificationDashboard(client: any) {
  const { data } = await client.get('/api/v1/gamification/me/dashboard/');
  return data;
}

export async function fetchMyLeaderboard(client: any, period: 'weekly' | 'monthly' | 'all_time' = 'weekly') {
  const { data } = await client.get('/api/v1/gamification/me/leaderboard/', { params: { period } });
  return data;
}

export async function fetchAdminGamificationOverview(client: any) {
  const { data } = await client.get('/api/v1/gamification/admin/overview/');
  return data;
}

export async function rebuildLeaderboards(client: any, period: 'weekly' | 'monthly' | 'all_time' = 'weekly') {
  const { data } = await client.post('/api/v1/gamification/admin/leaderboards/rebuild/', { period });
  return data;
}
