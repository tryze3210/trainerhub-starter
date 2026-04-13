export async function fetchAdminDisputeOverview(client: any) {
  const { data } = await client.get('/api/v1/disputes/admin/overview/');
  return data;
}

export async function fetchAdminDisputeQueue(client: any, params: Record<string, string>) {
  const { data } = await client.get('/api/v1/disputes/admin/queue/', { params });
  return data;
}

export async function createMyDispute(client: any, payload: Record<string, unknown>) {
  const { data } = await client.post('/api/v1/disputes/me/', payload);
  return data;
}

export async function fetchMyDisputes(client: any) {
  const { data } = await client.get('/api/v1/disputes/me/');
  return data;
}
