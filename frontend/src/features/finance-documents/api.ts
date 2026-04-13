export async function fetchMyFinanceDocuments(client: any) {
  const { data } = await client.get('/api/v1/finance-documents/me/documents/');
  return data;
}

export async function buildMyStatement(client: any) {
  const { data } = await client.post('/api/v1/finance-documents/me/statements/build/');
  return data;
}

export async function fetchAdminFinanceDocuments(client: any) {
  const { data } = await client.get('/api/v1/finance-documents/admin/documents/');
  return data;
}
