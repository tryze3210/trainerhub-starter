import Link from "next/link";
import { accountApi, onboardingApi } from "@/lib/api";
import { RoleSwitcher } from "./role-switcher";

export const metadata = {
  title: "Cabinet | TrainerHub",
  description: "Unified authenticated entrypoint for current account role.",
};

export default async function CabinetPage() {
  const [cabinet, onboarding] = await Promise.all([
    accountApi.cabinet(),
    onboardingApi.status(),
  ]);

  return (
    <main className="mx-auto max-w-6xl space-y-8 p-8">
      <section className="space-y-3">
        <h1 className="text-4xl font-bold">Cabinet</h1>
        <p className="text-slate-600">Role-aware entrypoint for authenticated user flows.</p>
        <div className="text-sm">
          Active role: <b>{cabinet.account.active_role}</b>
        </div>
        <RoleSwitcher roles={cabinet.account.available_roles ?? []} activeRole={cabinet.account.active_role ?? "user"} />
      </section>

      <section className="grid gap-4 md:grid-cols-4">
        <div className="rounded-2xl border p-4">
          <div className="text-sm text-slate-500">Favorites</div>
          <div className="text-3xl font-semibold">{cabinet.stats.favorites_count}</div>
        </div>
        <div className="rounded-2xl border p-4">
          <div className="text-sm text-slate-500">Access rights</div>
          <div className="text-3xl font-semibold">{cabinet.stats.active_entitlements_count}</div>
        </div>
        <div className="rounded-2xl border p-4">
          <div className="text-sm text-slate-500">Draft content</div>
          <div className="text-3xl font-semibold">{cabinet.stats.draft_content_count}</div>
        </div>
        <div className="rounded-2xl border p-4">
          <div className="text-sm text-slate-500">Unread notifications</div>
          <div className="text-3xl font-semibold">{cabinet.stats.unread_notifications_count}</div>
        </div>
      </section>

      <section className="grid gap-6 md:grid-cols-2">
        <div className="rounded-2xl border p-5">
          <h2 className="text-xl font-semibold">Capabilities</h2>
          <div className="mt-4 flex flex-wrap gap-2">
            {cabinet.role_capabilities.map((item) => (
              <span key={item} className="rounded-full border px-3 py-1 text-sm">{item}</span>
            ))}
          </div>
        </div>

        <div className="rounded-2xl border p-5">
          <h2 className="text-xl font-semibold">Onboarding</h2>
          <div className="mt-2 text-sm text-slate-600">
            {onboarding.summary.completed_steps}/{onboarding.summary.total_steps} complete · {onboarding.summary.completion_percent}%
          </div>
          <div className="mt-3 text-sm">
            Next step: <b>{onboarding.summary.next_step ?? "done"}</b>
          </div>
          <Link href="/onboarding" className="mt-4 inline-block text-sm underline">Open onboarding</Link>
        </div>
      </section>

      <section className="rounded-2xl border p-5">
        <h2 className="text-xl font-semibold">Quick links</h2>
        <div className="mt-4 grid gap-3 md:grid-cols-3">
          {cabinet.quick_links.map((link) => (
            <Link key={link.href} href={link.href} className="rounded-xl border p-4 text-sm hover:bg-slate-50">
              {link.label}
            </Link>
          ))}
        </div>
      </section>
    </main>
  );
}
