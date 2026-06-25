import { apiRequest } from '@/lib/api-client';
import type { ContentRuntimePayload } from '@/types/api';

export const contentRuntimeApi = {
  openProgramLesson: (programSlug: string, lessonRef: string) =>
    apiRequest<ContentRuntimePayload>(
      `/content/runtime/programs/${encodeURIComponent(programSlug)}/lessons/${encodeURIComponent(lessonRef)}/`,
      { auth: true }
    ),

  openCourseLesson: (courseId: string, lessonId: string) =>
    apiRequest<ContentRuntimePayload>(
      `/content/runtime/courses/${encodeURIComponent(courseId)}/lessons/${encodeURIComponent(lessonId)}/`,
      { auth: true }
    ),
};
