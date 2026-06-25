import { apiRequest } from '@/lib/api-client';

export type LessonProgressPayload = {
  id: string;
  lesson_id: string;
  program_id: string;
  content_type: 'program' | 'course' | string;
  is_completed: boolean;
  completed_at?: string | null;
  updated_at?: string | null;
};

export const progressApi = {
  completeLesson: (payload: { lesson_id: string; program_id?: string; content_type?: 'program' | 'course' }) =>
    apiRequest<LessonProgressPayload>('/progress/lessons/complete/', {
      auth: true,
      method: 'POST',
      body: JSON.stringify(payload),
    }),
};
