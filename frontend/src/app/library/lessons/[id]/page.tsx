import { PageHeader } from '@/components/page-header';
import { getLessonContent } from '@/lib/api';
import { CompleteLessonButton } from './complete-lesson-button';

export default async function LibraryLessonDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const lesson = await getLessonContent(id);
  return (
    <div className="space-y-6">
      <PageHeader title={lesson.title} description={lesson.description} />
      <div className="rounded-2xl border p-4 space-y-3">
        <div className="text-sm text-gray-600">program: {lesson.program_id}</div>
        <div className="text-sm text-gray-600">stream: {lesson.stream_url}</div>
        <CompleteLessonButton lessonId={lesson.id} />
      </div>
    </div>
  );
}
