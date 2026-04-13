export async function fetchReferralDashboard(client: any) {
  const { data } = await client.get('/api/v1/referrals/me/dashboard/');
  return data;
}

export async function fetchReferralInvites(client: any) {
  const { data } = await client.get('/api/v1/referrals/me/invites/');
  return data;
}

export async function fetchReferralRewards(client: any) {
  const { data } = await client.get('/api/v1/referrals/me/rewards/');
  return data;
}

export async function generateReferralCode(client: any, program_slug: string) {
  const { data } = await client.post('/api/v1/referrals/me/generate-code/', { program_slug });
  return data;
}
