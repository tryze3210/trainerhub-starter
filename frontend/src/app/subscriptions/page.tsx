import { commerceApi } from '@/lib/api';

export default async function SubscriptionsPage() {
  const data = await commerceApi.listSubscriptions();
  const subscriptions = data.results || data;

  return (
    <main>
      <h1>Subscriptions</h1>
      <pre>{JSON.stringify(subscriptions, null, 2)}</pre>
    </main>
  );
}
