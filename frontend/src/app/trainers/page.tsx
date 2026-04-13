import Link from "next/link";
import { publicTrainerApi } from "@/lib/api";

export const metadata = {
  title: "Trainers | TrainerHub",
  description: "Browse public trainer profiles on TrainerHub.",
};

export default async function TrainersPage() {
  const trainers = await publicTrainerApi.list();

  return (
    <main className="mx-auto max-w-5xl p-8 space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Trainers</h1>
        <p className="text-slate-600">Marketplace landing pages for coaches and studios.</p>
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        {trainers.map((trainer) => (
          <Link key={trainer.id} href={`/trainers/${trainer.slug}`} className="rounded-2xl border p-4 hover:shadow">
            <div className="text-xl font-semibold">{trainer.display_name}</div>
            <div className="text-sm text-slate-600">{trainer.headline}</div>
            <div className="mt-2 text-sm">{trainer.rating}★ · {trainer.reviews_count} reviews · {trainer.active_products_count} active products</div>
          </Link>
        ))}
      </div>
    </main>
  );
}
