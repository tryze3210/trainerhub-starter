import Link from "next/link";

export default function UnauthorizedPage() {
  return (
    <main className="p-8 space-y-4">
      <h1 className="text-3xl font-semibold">Access denied</h1>
      <p className="text-sm text-gray-600">Current role or onboarding state does not satisfy policy requirements for this section.</p>
      <div className="flex gap-4 text-sm underline">
        <Link href="/access">Open access matrix</Link>
        <Link href="/onboarding">Open onboarding</Link>
        <Link href="/cabinet">Back to cabinet</Link>
      </div>
    </main>
  );
}
