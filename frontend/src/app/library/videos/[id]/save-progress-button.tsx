'use client';

import { useState } from 'react';
import { saveVideoProgress } from '@/lib/api';

export function SaveProgressButton({ videoId, durationSeconds }: { videoId: string; durationSeconds: number }) {
  const [state, setState] = useState('');

  return (
    <button
      className="rounded-xl border px-4 py-2 text-sm font-medium"
      onClick={async () => {
        const watched = Math.max(60, Math.floor(durationSeconds * 0.9));
        const result = await saveVideoProgress(videoId, watched, watched);
        setState(`Saved ${result.completion_percent}%`);
      }}
    >
      Save 90% progress {state ? `· ${state}` : ''}
    </button>
  );
}
