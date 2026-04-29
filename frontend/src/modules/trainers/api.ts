import { apiRequest } from '@/lib/api-client';
import type {
  TrainerApplication,
  TrainerApplicationPayload,
  TrainerBusinessDashboard,
  TrainerCmsDashboard,
  TrainerProfile,
} from '@/types/api';

export const trainersApi = {
  listTrainers: () => apiRequest<TrainerProfile[]>('/trainers/'),
  getTrainer: (slug: string) => apiRequest<TrainerProfile>(`/trainers/${slug}/`),
  getMyApplication: () =>
    apiRequest<TrainerApplication>('/trainers/me/application/', {
      auth: true,
    }),
  updateMyApplication: (payload: TrainerApplicationPayload) =>
    apiRequest<TrainerApplication>('/trainers/me/application/', {
      auth: true,
      method: 'PATCH',
      body: JSON.stringify(payload),
    }),
  submitMyApplication: (payload: TrainerApplicationPayload = {}) =>
    apiRequest<TrainerApplication>('/trainers/me/application/submit/', {
      auth: true,
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  getMyProfile: () => apiRequest<TrainerProfile>('/trainers/me/profile/', { auth: true }),
  createMyProfile: (payload: Partial<TrainerProfile>) =>
    apiRequest<TrainerProfile>('/trainers/me/profile/', {
      auth: true,
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  updateMyProfile: (payload: Partial<TrainerProfile>) =>
    apiRequest<TrainerProfile>('/trainers/me/profile/', {
      auth: true,
      method: 'PATCH',
      body: JSON.stringify(payload),
    }),
  getTrainerCmsDashboard: () =>
    apiRequest<TrainerCmsDashboard | TrainerCmsDashboard[]>('/trainer-cms/dashboard/', {
      auth: true,
    }),
  getTrainerBusinessDashboard: (days = 30) =>
    apiRequest<TrainerBusinessDashboard>(`/trainer-cms/business-dashboard/?days=${days}`, {
      auth: true,
    }),
};
