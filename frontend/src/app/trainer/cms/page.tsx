import Link from "next/link";
import { accessApi, trainerCmsApi } from "@/lib/api";
import { redirect } from "next/navigation";

export default async function TrainerCmsPage() {
  const access = await accessApi.snapshot();
  const gate = access.feature_gates.trainer_cms;
  if (!gate?.enabled) {
    redirect("/unauthorized");
  }

  const dashboard = await trainerCmsApi.dashboard();

  return (
    <main className="p-8 space-y-6">
      <h1 className="text-3xl font-semibold">Trainer CMS</h1>
      <div className="grid gap-4 md:grid-cols-3">
        <div className="border rounded-xl p-4">Videos: {dashboard.videos.length}</div>
        <div className="border rounded-xl p-4">Programs: {dashboard.programs.length}</div>
        <div className="border rounded-xl p-4">Bundles: {dashboard.bundles.length}</div>
      </div>
      <Link className="underline text-sm" href="/access">Policy source: /access</Link>
    </main>
  );
}
