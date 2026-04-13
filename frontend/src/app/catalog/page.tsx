import Link from "next/link";
import { publicCatalogApi } from "@/lib/api";

export const metadata = {
  title: "Catalog | TrainerHub",
  description: "Discover videos, programs and bundles from trainers on TrainerHub.",
};

export default async function CatalogPage({ searchParams }: { searchParams?: Promise<Record<string, string>> }) {
  const params = (await searchParams) ?? {};
  const data = await publicCatalogApi.list(params);

  return (
    <main className="mx-auto max-w-6xl p-8 space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Catalog</h1>
        <p className="text-slate-600">Search, filter and sort the public marketplace inventory.</p>
      </div>

      <div className="rounded-2xl border p-4 text-sm text-slate-700">
        Applied sort: <b>{data.applied_filters.sort ?? "newest"}</b> · Results: <b>{data.count}</b>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        {data.items.map((item) => (
          <Link key={item.id} href={`/catalog/${item.entity_type}/${item.slug}`} className="rounded-2xl border p-4 hover:shadow">
            <div className="text-xs uppercase text-slate-500">{item.entity_type}</div>
            <div className="mt-2 text-lg font-semibold">{item.title}</div>
            <div className="text-sm text-slate-600">{item.trainer_name}</div>
            <div className="mt-2 text-sm">{item.category} · {item.difficulty}</div>
            <div className="mt-3 text-sm">€{item.price} · {item.rating}★ · {item.reviews_count} reviews</div>
          </Link>
        ))}
      </div>
    </main>
  );
}
