import { commerceApi } from '@/lib/api';

export default async function OrdersPage() {
  const data = await commerceApi.listOrders();
  const orders = data.results || data;

  return (
    <main>
      <h1>Orders</h1>
      <pre>{JSON.stringify(orders, null, 2)}</pre>
    </main>
  );
}
