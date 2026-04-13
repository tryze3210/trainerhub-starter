export default function AffiliatePartnerDashboardPage() {
  const summary = { clicks: 1240, signups: 205, orders: 84, commission: "₽28,840" };

  return (
    <main className="p-8 space-y-6">
      <div>
        <h1 className="text-3xl font-semibold">Partner Dashboard</h1>
        <p className="text-sm text-gray-500">Track clicks, conversions, attributed orders, and pending commission.</p>
      </div>

      <div className="grid md:grid-cols-4 gap-4">
        <div className="border rounded-2xl p-5"><div className="text-xs text-gray-500">Clicks</div><div className="text-2xl font-semibold">{summary.clicks}</div></div>
        <div className="border rounded-2xl p-5"><div className="text-xs text-gray-500">Signups</div><div className="text-2xl font-semibold">{summary.signups}</div></div>
        <div className="border rounded-2xl p-5"><div className="text-xs text-gray-500">Orders</div><div className="text-2xl font-semibold">{summary.orders}</div></div>
        <div className="border rounded-2xl p-5"><div className="text-xs text-gray-500">Pending commission</div><div className="text-2xl font-semibold">{summary.commission}</div></div>
      </div>
    </main>
  );
}
