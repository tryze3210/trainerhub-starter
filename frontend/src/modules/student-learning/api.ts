import { apiRequest } from '@/lib/api-client';
import type { StudentLearningAreaPayload } from '@/types/api';

export const studentLearningApi = {
  getLearningArea: () =>
    apiRequest<StudentLearningAreaPayload>('/content/student/learning-area/', {
      auth: true,
    }),
};
