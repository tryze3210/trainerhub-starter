import { apiRequest } from '@/lib/api-client';
import type {
  Assignment,
  AssignmentReviewPayload,
  AssignmentSubmitPayload,
  AssignmentTrainerCreatePayload,
  AssignmentsPayload,
  AssignmentSubmissionsPayload,
} from '@/types/api';

export const assignmentsApi = {
  getStudentAssignments: () =>
    apiRequest<AssignmentsPayload>('/assignments/student/', {
      auth: true,
    }),

  submitAssignment: (assignmentId: string, payload: AssignmentSubmitPayload) =>
    apiRequest<Assignment>(`/assignments/student/${assignmentId}/submit/`, {
      auth: true,
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  getTrainerAssignments: () =>
    apiRequest<AssignmentsPayload>('/assignments/trainer/', {
      auth: true,
    }),

  createAssignment: (payload: AssignmentTrainerCreatePayload) =>
    apiRequest<Assignment>('/assignments/trainer/', {
      auth: true,
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  getTrainerSubmissions: () =>
    apiRequest<AssignmentSubmissionsPayload>('/assignments/trainer/submissions/', {
      auth: true,
    }),

  reviewSubmission: (submissionId: string, payload: AssignmentReviewPayload) =>
    apiRequest<Assignment>(`/assignments/trainer/submissions/${submissionId}/review/`, {
      auth: true,
      method: 'POST',
      body: JSON.stringify(payload),
    }),
};
