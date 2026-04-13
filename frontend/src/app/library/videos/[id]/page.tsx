import { PageHeader } from '@/components/page-header';
import { getVideoContent } from '@/lib/api';
import { SaveProgressButton } from './save-progress-button';

export default async function LibraryVideoDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const video = await getVideoContent(id);
  return (
    <div className="space-y-6">
      <PageHeader title={video.title} description={video.description} />
      <div className="rounded-2xl border p-4 space-y-3">
        <div className="text-sm text-gray-600">stream: {video.stream_url}</div>
        <div className="text-sm text-gray-600">duration: {video.duration_seconds} sec</div>
        <SaveProgressButton videoId={video.id} durationSeconds={video.duration_seconds} />
      </div>
    </div>
  );
}
