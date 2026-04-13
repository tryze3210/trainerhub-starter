import { commerceApi } from '@/lib/api';

export default async function EntitlementsPage() {
  const data = await commerceApi.listEntitlements();
  const entitlements = data.results || data;

  return (
    <main>
      <h1>Entitlements</h1>
      <pre>{JSON.stringify(entitlements, null, 2)}</pre>
    </main>
  );
}
