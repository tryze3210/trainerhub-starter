'use client';

import { useState } from 'react';
import { completeLesson } from '@/lib/api';

export function CompleteLessonButton({ lessonId }: { lessonId: string }) {
  const [state, setState] = useState('');
  return (
    <button
      className="rounded-xl border px-4 py-2 text-sm font-medium"
      onClick={async () => {
        await completeLesson(lessonId);
        setState('Completed');
      }}
    >
      Mark lesson complete {state ? `· ${state}` : ''}
    </button>
  );
}
