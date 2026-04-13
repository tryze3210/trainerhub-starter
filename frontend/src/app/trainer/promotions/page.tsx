async function getTrainerCampaigns() {
  const res = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/trainer/promotions/campaigns/`, {
    headers: {
      "Content-Type": "application/json",
    },
    cache: "no-store",
  });

  if (!res.ok) {
    throw new Error("Failed to load trainer campaigns");
  }

  return res.json();
}

export default async function TrainerPromotionsPage() {
  const campaigns = await getTrainerCampaigns();

  return (
    <main className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Мои промокампании</h1>
        <p className="text-sm text-neutral-600">Скидки, которые влияют на твой net revenue.</p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {campaigns.results?.map((item: any) => (
          <article key={item.id} className="rounded-2xl border border-neutral-200 bg-white p-5 shadow-sm">
            <h2 className="text-lg font-semibold">{item.name}</h2>
            <div className="mt-3 space-y-1 text-sm text-neutral-700">
              <p>Status: {item.status}</p>
              <p>Funding: {item.funding_source}</p>
              <p>Starts: {item.starts_at}</p>
              <p>Ends: {item.ends_at || "—"}</p>
              <p>Redemptions: {item.redemptions_count ?? 0}</p>
            </div>
          </article>
        ))}
      </div>
    </main>
  );
}
