import Link from "next/link";
import { publicCatalogApi, reviewsApi } from "@/lib/api";

export async function generateMetadata({ params }: { params: Promise<{ entityType: string; slug: string }> }) {
  const { entityType, slug } = await params;
  const item = await publicCatalogApi.detail(entityType, slug);
  return {
    title: `${item.title} | TrainerHub`,
    description: item.description,
  };
}

export default async function CatalogDetailPage({ params }: { params: Promise<{ entityType: string; slug: string }> }) {
  const { entityType, slug } = await params;
  const [item, reviews] = await Promise.all([
    publicCatalogApi.detail(entityType, slug),
    reviewsApi.byTarget(entityType, slug),
  ]);

  return (
    <main className="mx-auto max-w-4xl p-8 space-y-8">
      <section className="space-y-3">
        <div className="text-xs uppercase text-slate-500">{item.entity_type}</div>
        <h1 className="text-4xl font-bold">{item.title}</h1>
        <p className="text-slate-600">{item.description}</p>
        <div className="text-sm">€{item.price} · {item.rating}★ · {item.reviews_count} reviews</div>
        <Link className="underline text-sm" href={`/trainers/${item.trainer_slug}`}>Open trainer profile: {item.trainer_name}</Link>
      </section>

      <section className="space-y-4">
        <h2 className="text-2xl font-semibold">Reviews</h2>
        <div className="rounded-2xl border p-4 text-sm">Average: <b>{reviews.summary.average_rating}</b> · Count: <b>{reviews.summary.reviews_count}</b></div>
        <div className="space-y-4">
          {reviews.items.map((review) => (
            <article key={review.id} className="rounded-2xl border p-4">
              <div className="font-semibold">{review.title}</div>
              <div className="text-sm text-slate-600">{review.author_name} · {review.rating}★</div>
              <p className="mt-2 text-sm">{review.body}</p>
            </article>
          ))}
        </div>
      </section>
    </main>
  );
}
