async function getCampaigns() {
  const res = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/admin/promotions/campaigns/`, {
    headers: {
      "Content-Type": "application/json",
    },
    cache: "no-store",
  });

  if (!res.ok) {
    throw new Error("Failed to load campaigns");
  }

  return res.json();
}

export default async function AdminPromotionsPage() {
  const campaigns = await getCampaigns();

  return (
    <main className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Promotions</h1>
        <p className="text-sm text-neutral-600">Управление promo campaigns и discount economics.</p>
      </div>

      <div className="rounded-2xl border border-neutral-200 bg-white overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-neutral-50 text-left">
            <tr>
              <th className="p-3">Name</th>
              <th className="p-3">Status</th>
              <th className="p-3">Funding</th>
              <th className="p-3">Starts</th>
              <th className="p-3">Ends</th>
            </tr>
          </thead>
          <tbody>
            {campaigns.results?.map((item: any) => (
              <tr key={item.id} className="border-t border-neutral-100">
                <td className="p-3">{item.name}</td>
                <td className="p-3">{item.status}</td>
                <td className="p-3">{item.funding_source}</td>
                <td className="p-3">{item.starts_at}</td>
                <td className="p-3">{item.ends_at || "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </main>
  );
}
