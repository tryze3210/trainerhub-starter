export default function AdminAffiliatesPage() {
  const mock = [
    { code: "BLOGGER10", partner: "Fitness Blogger Anna", clicks: 1240, orders: 84, gross: "₽412,000", commission: "₽28,840" },
    { code: "INSTAIVAN", partner: "Ivan Reels", clicks: 860, orders: 41, gross: "₽205,500", commission: "₽14,385" },
  ];

  return (
    <main className="p-8 space-y-6">
      <div>
        <h1 className="text-3xl font-semibold">Affiliate Attribution</h1>
        <p className="text-sm text-gray-500">Admin dashboard for referral partners, attributed orders, and commission exposure.</p>
      </div>

      <div className="border rounded-2xl overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50">
            <tr>
              <th className="text-left p-4">Code</th>
              <th className="text-left p-4">Partner</th>
              <th className="text-left p-4">Clicks</th>
              <th className="text-left p-4">Orders</th>
              <th className="text-left p-4">Attributed GMV</th>
              <th className="text-left p-4">Commission</th>
            </tr>
          </thead>
          <tbody>
            {mock.map((row) => (
              <tr key={row.code} className="border-t">
                <td className="p-4 font-medium">{row.code}</td>
                <td className="p-4">{row.partner}</td>
                <td className="p-4">{row.clicks}</td>
                <td className="p-4">{row.orders}</td>
                <td className="p-4">{row.gross}</td>
                <td className="p-4">{row.commission}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </main>
  );
}
