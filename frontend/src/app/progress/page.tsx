import { PageHeader } from '@/components/page-header';
import { ProgressCard } from '@/components/progress-card';
import { getLessonProgress, getProgramProgress, getProgressSummary, getVideoProgress } from '@/lib/api';

export default async function ProgressPage() {
  const [summary, videos, lessons, programs] = await Promise.all([
    getProgressSummary(),
    getVideoProgress(),
    getLessonProgress(),
    getProgramProgress(),
  ]);

  return (
    <div className="space-y-6">
      <PageHeader title="Progress" description="Consumption analytics and completion state resolved from user activity." />
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <ProgressCard title="Watched seconds" value={summary.watched_seconds} description="Aggregated video watch time." />
        <ProgressCard title="Completed videos" value={summary.completed_videos} description="Videos at 90%+ completion." />
        <ProgressCard title="Completed lessons" value={summary.completed_lessons} description="Lesson milestones already closed." />
        <ProgressCard title="Completed programs" value={summary.completed_programs} description="Programs with all lessons completed." />
      </div>
      <div className="grid gap-6 xl:grid-cols-3">
        <div className="rounded-2xl border p-4">
          <div className="font-semibold">Video progress</div>
          <div className="mt-3 space-y-3">
            {videos.map((item) => (
              <div key={item.id} className="rounded-xl border p-3 text-sm">
                <div>video: {item.video_id}</div>
                <div>completion: {item.completion_percent}%</div>
              </div>
            ))}
          </div>
        </div>
        <div className="rounded-2xl border p-4">
          <div className="font-semibold">Lesson progress</div>
          <div className="mt-3 space-y-3">
            {lessons.map((item) => (
              <div key={item.id} className="rounded-xl border p-3 text-sm">
                <div>lesson: {item.lesson_id}</div>
                <div>{item.is_completed ? 'completed' : 'in progress'}</div>
              </div>
            ))}
          </div>
        </div>
        <div className="rounded-2xl border p-4">
          <div className="font-semibold">Program progress</div>
          <div className="mt-3 space-y-3">
            {programs.map((item) => (
              <div key={item.id} className="rounded-xl border p-3 text-sm">
                <div>program: {item.program_id}</div>
                <div>{item.completed_lessons}/{item.total_lessons} lessons</div>
                <div>completion: {item.completion_percent}%</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
