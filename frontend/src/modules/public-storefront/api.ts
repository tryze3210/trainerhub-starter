import { apiRequest, normalizeListResponse } from '@/lib/api-client';
import type { PublicBundle, PublicProgram, PublicVideo, TrainerProfile } from '@/types/api';

export type StorefrontEntityType = 'video' | 'program' | 'bundle';

export type StorefrontItem = {
  id: string;
  slug: string;
  title: string;
  description?: string;
  short_description?: string;
  category?: string;
  difficulty?: string;
  price_amount?: string;
  price?: string;
  currency?: string;
  duration_minutes?: number;
  trainer_slug?: string;
  trainer_name?: string;
  is_featured?: boolean;
  is_active?: boolean;
  entity_type: StorefrontEntityType;
};

export type StorefrontFilters = {
  query?: string;
  type?: 'all' | StorefrontEntityType;
  trainerSlug?: string;
};

export type StorefrontSeoPayload = {
  title: string;
  description: string;
  canonicalPath: string;
};

function withEntityType<T extends PublicVideo | PublicProgram | PublicBundle>(
  item: T,
  entityType: StorefrontEntityType
): StorefrontItem {
  return {
    ...item,
    entity_type: entityType,
    price: item.price_amount,
  };
}

function byTrainerSlug(items: StorefrontItem[], trainerSlug?: string): StorefrontItem[] {
  if (!trainerSlug) return items;
  return items.filter((item) => item.trainer_slug === trainerSlug);
}

export function getStorefrontTitle(item: Partial<StorefrontItem> | null | undefined): string {
  return item?.title || 'Без названия';
}

export function getStorefrontDescription(item: Partial<StorefrontItem> | null | undefined): string {
  return item?.short_description || item?.description || 'Описание пока не заполнено.';
}

export function getStorefrontPrice(item: Partial<StorefrontItem> | null | undefined): string {
  const value = item?.price_amount ?? item?.price;
  if (!value || value === '0.00' || value === '0') return 'Бесплатно';
  return `${value} ${item?.currency || 'RUB'}`;
}

export function getStorefrontHref(item: StorefrontItem): string {
  if (item.entity_type === 'video') return `/catalog/videos/${item.slug}`;
  if (item.entity_type === 'program') return `/catalog/programs/${item.slug}`;
  return `/catalog/bundles/${item.slug}`;
}

export function buildContentCheckoutHref(item: StorefrontItem): string {
  const params = new URLSearchParams({
    item_type: item.entity_type,
    item_id: item.id,
    title: item.title,
    amount: String(item.price_amount || item.price || ''),
    currency: item.currency || 'RUB',
  });
  return `/login?next=${encodeURIComponent(`/checkout?${params.toString()}`)}`;
}

export const publicStorefrontApi = {
  async listVideos(): Promise<PublicVideo[]> {
    const payload = await apiRequest<PublicVideo[] | { results: PublicVideo[] }>('/content/videos/');
    return normalizeListResponse<PublicVideo>(payload);
  },

  getVideo(slug: string): Promise<PublicVideo> {
    return apiRequest<PublicVideo>(`/content/videos/${encodeURIComponent(slug)}/`);
  },

  async listPrograms(): Promise<PublicProgram[]> {
    const payload = await apiRequest<PublicProgram[] | { results: PublicProgram[] }>('/content/programs/');
    return normalizeListResponse<PublicProgram>(payload);
  },

  getProgram(slug: string): Promise<PublicProgram> {
    return apiRequest<PublicProgram>(`/content/programs/${encodeURIComponent(slug)}/`);
  },

  async listBundles(): Promise<PublicBundle[]> {
    const payload = await apiRequest<PublicBundle[] | { results: PublicBundle[] }>('/content/bundles/');
    return normalizeListResponse<PublicBundle>(payload);
  },

  getBundle(slug: string): Promise<PublicBundle> {
    return apiRequest<PublicBundle>(`/content/bundles/${encodeURIComponent(slug)}/`);
  },

  async listTrainers(): Promise<TrainerProfile[]> {
    const payload = await apiRequest<TrainerProfile[] | { results: TrainerProfile[] }>('/trainers/');
    return normalizeListResponse<TrainerProfile>(payload);
  },

  getTrainer(slug: string): Promise<TrainerProfile> {
    return apiRequest<TrainerProfile>(`/trainers/${encodeURIComponent(slug)}/`);
  },

  async listCatalog(filters: StorefrontFilters = {}): Promise<StorefrontItem[]> {
    const [videos, programs, bundles] = await Promise.all([
      this.listVideos(),
      this.listPrograms(),
      this.listBundles(),
    ]);

    const merged: StorefrontItem[] = [
      ...videos.map((item) => withEntityType(item, 'video')),
      ...programs.map((item) => withEntityType(item, 'program')),
      ...bundles.map((item) => withEntityType(item, 'bundle')),
    ];

    const scoped = byTrainerSlug(merged, filters.trainerSlug);
    const q = (filters.query || '').trim().toLowerCase();

    return scoped.filter((item) => {
      const matchesType = !filters.type || filters.type === 'all' ? true : item.entity_type === filters.type;
      const haystack = [
        item.title,
        item.description,
        item.category,
        item.difficulty,
        item.trainer_name,
        item.entity_type,
      ]
        .filter(Boolean)
        .join(' ')
        .toLowerCase();

      return matchesType && (q ? haystack.includes(q) : true);
    });
  },
};
