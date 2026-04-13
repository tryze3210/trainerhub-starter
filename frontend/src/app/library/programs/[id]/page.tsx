import Link from 'next/link';
import { PageHeader } from '@/components/page-header';
import { getProgramContent } from '@/lib/api';

export default async function LibraryProgramDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const program = await getProgramContent(id);
  return (
    <div className="space-y-6">
      <PageHeader title={program.title} description={program.description} />
      <div className="space-y-3">
        {program.lessons.map((lesson) => (
          <Link key={lesson.id} href={`/library/lessons/${lesson.id}`} className="block rounded-2xl border p-4 hover:bg-gray-50">
            <div className="font-semibold">#{lesson.position} {lesson.title}</div>
            <div className="text-sm text-gray-600">{lesson.duration_seconds} sec</div>
          </Link>
        ))}
      </div>
    </div>
  );
}
