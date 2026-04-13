import Link from 'next/link';
import { PageHeader } from '@/components/page-header';
import { getResolvedLibrary } from '@/lib/api';

export default async function LibraryPage() {
  const items = await getResolvedLibrary();
  return (
    <div className="space-y-6">
      <PageHeader title="My library" description="Resolved content library based on active entitlements." />
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {items.map((item) => {
          const href = item.kind === 'video' ? `/library/videos/${item.id}` : `/library/programs/${item.id}`;
          return (
            <Link key={`${item.kind}-${item.id}`} href={href} className="rounded-2xl border p-4 hover:bg-gray-50">
              <div className="text-xs uppercase tracking-wide text-gray-500">{item.kind}</div>
              <div className="mt-2 font-semibold">{item.title}</div>
              <div className="mt-1 text-sm text-gray-600">trainer: {item.trainer_id}</div>
              <div className="mt-1 text-sm text-gray-500">source: {item.source}</div>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
