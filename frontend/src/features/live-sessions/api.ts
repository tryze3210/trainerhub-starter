export async function fetchAdminLiveOverview(client: { get: (url: string) => Promise<any> }) {
  return client.get('/api/v1/live/admin/overview/');
}

export async function fetchMyLiveSessions(client: { get: (url: string) => Promise<any> }) {
  return client.get('/api/v1/live/me/sessions/');
}
