import Link from "next/link";
import { publicTrainerApi, reviewsApi } from "@/lib/api";

export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const trainer = await publicTrainerApi.detail(slug);
  return {
    title: `${trainer.display_name} | TrainerHub`,
    description: trainer.bio,
  };
}

export default async function TrainerProfilePage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const [trainer, reviews] = await Promise.all([
    publicTrainerApi.detail(slug),
    reviewsApi.byTarget("trainer", slug),
  ]);

  return (
    <main className="mx-auto max-w-5xl p-8 space-y-8">
      <section className="space-y-3">
        <h1 className="text-4xl font-bold">{trainer.display_name}</h1>
        <p className="text-slate-600">{trainer.headline}</p>
        <p>{trainer.bio}</p>
        <div className="text-sm">{trainer.rating}★ · {trainer.reviews_count} reviews · {trainer.students_count} students</div>
        <div className="flex flex-wrap gap-2 text-sm">
          {trainer.specialties.map((item) => <span key={item} className="rounded-full border px-3 py-1">{item}</span>)}
        </div>
      </section>

      <section className="space-y-4">
        <h2 className="text-2xl font-semibold">Products</h2>
        <div className="grid gap-4 md:grid-cols-2">
          {trainer.catalog_items.map((item) => (
            <Link key={item.id} href={`/catalog/${item.entity_type}/${item.slug}`} className="rounded-2xl border p-4 hover:shadow">
              <div className="text-xs uppercase text-slate-500">{item.entity_type}</div>
              <div className="mt-1 font-semibold">{item.title}</div>
              <div className="text-sm text-slate-600">{item.category} · {item.difficulty}</div>
              <div className="mt-2 text-sm">€{item.price} · {item.rating}★</div>
            </Link>
          ))}
        </div>
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
