import Link from "next/link";

const links = [
  { href: "/catalog", label: "Public catalog" },
  { href: "/trainers", label: "Trainers" },
  { href: "/cabinet", label: "Cabinet" },
  { href: "/access", label: "Access snapshot" },
  { href: "/tenancy", label: "Tenancy" },
  { href: "/workflows", label: "Workflows" },
  { href: "/events", label: "Events" },
  { href: "/projections", label: "Projections" },
  { href: "/observability", label: "Observability" },
  { href: "/ops/diagnostics", label: "Ops diagnostics" },
];

export default function HomePage() {
  return (
    <main className="p-8 space-y-6">
      <section>
        <h1 className="text-3xl font-semibold">TrainerHub</h1>
        <p className="text-sm text-gray-600">v14 scaffold with observability, correlation-aware troubleshooting and ops diagnostics.</p>
      </section>
      <div className="grid md:grid-cols-2 gap-4">
        {links.map((item) => (
          <Link key={item.href} href={item.href} className="rounded-2xl border p-4 hover:bg-gray-50">
            <div className="font-medium">{item.label}</div>
            <div className="text-sm text-gray-600">{item.href}</div>
          </Link>
        ))}
      </div>
    </main>
  );
}
