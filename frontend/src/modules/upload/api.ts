import { apiRequest, normalizeListResponse } from '@/lib/api-client';
import type {
  BundleDraft,
  BundleItemDraft,
  MediaAsset,
  ProgramDraft,
  ProgramLessonDraft,
  UploadIntentResponse,
  VideoDraft,
} from '@/types/api';

export const uploadApi = {
  createUploadIntent: (payload: {
    filename: string;
    content_type: string;
    file_size_bytes: number;
    visibility: 'private' | 'public';
  }) =>
    apiRequest<UploadIntentResponse>('/videos/upload-intents/', {
      auth: true,
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  completeUploadIntent: (mediaAssetId: string, checksumSha256?: string) =>
    apiRequest<{ media_asset_id: string; status: string }>(`/videos/upload-intents/${mediaAssetId}/complete/`, {
      auth: true,
      method: 'POST',
      body: JSON.stringify({
        checksum_sha256: checksumSha256 || '',
      }),
    }),

  getMediaAsset: (mediaAssetId: string) =>
    apiRequest<MediaAsset>(`/videos/media-assets/${mediaAssetId}/`, {
      auth: true,
    }),

  createVideoDraft: (payload: {
    title: string;
    slug: string;
    description: string;
    video_asset_id?: string | null;
    price_amount?: string;
    currency?: string;
  }) =>
    apiRequest<VideoDraft>('/trainer-cms/videos/', {
      auth: true,
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  updateVideoDraft: (
    draftId: string,
    payload: Partial<{
      title: string;
      slug: string;
      description: string;
      video_asset_id: string | null;
      price_amount: string;
      currency: string;
    }>
  ) =>
    apiRequest<VideoDraft>(`/trainer-cms/videos/${draftId}/`, {
      auth: true,
      method: 'PATCH',
      body: JSON.stringify(payload),
    }),

  submitVideoDraft: (draftId: string) =>
    apiRequest<VideoDraft>(`/trainer-cms/videos/${draftId}/submit/`, {
      auth: true,
      method: 'POST',
      body: JSON.stringify({}),
    }),

  publishVideoDraft: (draftId: string) =>
    apiRequest<VideoDraft>(`/trainer-cms/videos/${draftId}/publish/`, {
      auth: true,
      method: 'POST',
      body: JSON.stringify({}),
    }),

  archiveVideoDraft: (draftId: string) =>
    apiRequest<VideoDraft>(`/trainer-cms/videos/${draftId}/archive/`, {
      auth: true,
      method: 'POST',
      body: JSON.stringify({}),
    }),

  async listMyVideos(): Promise<VideoDraft[]> {
    const payload = await apiRequest<VideoDraft[] | { results: VideoDraft[] }>('/trainer-cms/videos/', {
      auth: true,
    });
    return normalizeListResponse(payload);
  },

  createProgramDraft: (payload: {
    title: string;
    slug: string;
    description: string;
    price_amount?: string;
    currency?: string;
  }) =>
    apiRequest<ProgramDraft>('/trainer-cms/programs/', {
      auth: true,
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  updateProgramDraft: (
    draftId: string,
    payload: Partial<{
      title: string;
      slug: string;
      description: string;
      price_amount: string;
      currency: string;
    }>
  ) =>
    apiRequest<ProgramDraft>(`/trainer-cms/programs/${draftId}/`, {
      auth: true,
      method: 'PATCH',
      body: JSON.stringify(payload),
    }),

  publishProgramDraft: (draftId: string) =>
    apiRequest<ProgramDraft>(`/trainer-cms/programs/${draftId}/publish/`, {
      auth: true,
      method: 'POST',
      body: JSON.stringify({}),
    }),

  async listMyPrograms(): Promise<ProgramDraft[]> {
    const payload = await apiRequest<ProgramDraft[] | { results: ProgramDraft[] }>('/trainer-cms/programs/', {
      auth: true,
    });
    return normalizeListResponse(payload);
  },

  async listProgramLessons(programId: string): Promise<ProgramLessonDraft[]> {
    const payload = await apiRequest<ProgramLessonDraft[] | { results: ProgramLessonDraft[] }>(
      `/trainer-cms/programs/${programId}/lessons/`,
      { auth: true }
    );
    return normalizeListResponse(payload);
  },

  createProgramLesson: (
    programId: string,
    payload: {
      title: string;
      description?: string;
      position: number;
      video_asset_id?: string | null;
      is_preview?: boolean;
    }
  ) =>
    apiRequest<ProgramLessonDraft>(`/trainer-cms/programs/${programId}/lessons/`, {
      auth: true,
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  updateProgramLesson: (
    programId: string,
    lessonId: string,
    payload: Partial<{
      title: string;
      description: string;
      position: number;
      video_asset_id: string | null;
      is_preview: boolean;
    }>
  ) =>
    apiRequest<ProgramLessonDraft>(`/trainer-cms/programs/${programId}/lessons/${lessonId}/`, {
      auth: true,
      method: 'PATCH',
      body: JSON.stringify(payload),
    }),

  deleteProgramLesson: (programId: string, lessonId: string) =>
    apiRequest<void>(`/trainer-cms/programs/${programId}/lessons/${lessonId}/`, {
      auth: true,
      method: 'DELETE',
    }),

  createBundleDraft: (payload: {
    title: string;
    slug: string;
    description: string;
    price_amount?: string;
    currency?: string;
  }) =>
    apiRequest<BundleDraft>('/trainer-cms/bundles/', {
      auth: true,
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  updateBundleDraft: (
    draftId: string,
    payload: Partial<{
      title: string;
      slug: string;
      description: string;
      price_amount: string;
      currency: string;
    }>
  ) =>
    apiRequest<BundleDraft>(`/trainer-cms/bundles/${draftId}/`, {
      auth: true,
      method: 'PATCH',
      body: JSON.stringify(payload),
    }),

  publishBundleDraft: (draftId: string) =>
    apiRequest<BundleDraft>(`/trainer-cms/bundles/${draftId}/publish/`, {
      auth: true,
      method: 'POST',
      body: JSON.stringify({}),
    }),

  async listMyBundles(): Promise<BundleDraft[]> {
    const payload = await apiRequest<BundleDraft[] | { results: BundleDraft[] }>('/trainer-cms/bundles/', {
      auth: true,
    });
    return normalizeListResponse(payload);
  },

  async listBundleItems(bundleId: string): Promise<BundleItemDraft[]> {
    const payload = await apiRequest<BundleItemDraft[] | { results: BundleItemDraft[] }>(
      `/trainer-cms/bundles/${bundleId}/items/`,
      { auth: true }
    );
    return normalizeListResponse(payload);
  },

  createBundleItem: (
    bundleId: string,
    payload: {
      item_type: 'video' | 'program';
      target_id: string;
      position: number;
    }
  ) =>
    apiRequest<BundleItemDraft>(`/trainer-cms/bundles/${bundleId}/items/`, {
      auth: true,
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  updateBundleItem: (
    bundleId: string,
    itemId: string,
    payload: Partial<{
      item_type: 'video' | 'program';
      target_id: string;
      position: number;
    }>
  ) =>
    apiRequest<BundleItemDraft>(`/trainer-cms/bundles/${bundleId}/items/${itemId}/`, {
      auth: true,
      method: 'PATCH',
      body: JSON.stringify(payload),
    }),

  deleteBundleItem: (bundleId: string, itemId: string) =>
    apiRequest<void>(`/trainer-cms/bundles/${bundleId}/items/${itemId}/`, {
      auth: true,
      method: 'DELETE',
    }),
};
