import { apiRequest, normalizeListResponse } from '@/lib/api-client';

export type TrainerProductItem = {
  id: string;
  video: string;
  video_id?: string;
  video_title?: string;
  video_status?: string;
  position: number;
};

export type ProductReadinessCheck = {
  code: string;
  title: string;
  status: 'pass' | 'blocker' | string;
  message: string;
};

export type ProductReadiness = {
  product_id: string;
  status: 'ready' | 'blocked' | string;
  blockers_count: number;
  checks: ProductReadinessCheck[];
};

export type TrainerProduct = {
  id: string;
  slug: string;
  title: string;
  description?: string;
  product_type: 'video' | 'bundle' | string;
  access_type: 'one_time' | 'subscription' | string;
  status: 'draft' | 'published' | 'archived' | string;
  currency: string;
  price_amount: string;
  items?: TrainerProductItem[];
  items_count?: number;
  readiness?: ProductReadiness | null;
  created_at?: string;
  updated_at?: string;
};

export type TrainerProductPayload = {
  title: string;
  slug?: string;
  description?: string;
  product_type?: 'video' | 'bundle';
  access_type?: 'one_time' | 'subscription';
  currency?: string;
  price_amount?: string;
  item_video_ids?: string[];
};

function productPath(productId?: string): string {
  return productId ? `/products/trainer/${productId}/` : '/products/trainer/';
}

export const trainerProductsApi = {
  async list(): Promise<TrainerProduct[]> {
    const payload = await apiRequest<TrainerProduct[] | { results: TrainerProduct[] }>(productPath(), { auth: true });
    return normalizeListResponse(payload);
  },

  get(productId: string): Promise<TrainerProduct> {
    return apiRequest<TrainerProduct>(productPath(productId), { auth: true });
  },

  create(payload: TrainerProductPayload): Promise<TrainerProduct> {
    return apiRequest<TrainerProduct>(productPath(), {
      auth: true,
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  update(productId: string, payload: Partial<TrainerProductPayload>): Promise<TrainerProduct> {
    return apiRequest<TrainerProduct>(productPath(productId), {
      auth: true,
      method: 'PATCH',
      body: JSON.stringify(payload),
    });
  },

  readiness(productId: string): Promise<ProductReadiness> {
    return apiRequest<ProductReadiness>(`/products/trainer/${productId}/readiness/`, { auth: true });
  },

  publish(productId: string): Promise<TrainerProduct> {
    return apiRequest<TrainerProduct>(`/products/trainer/${productId}/publish/`, {
      auth: true,
      method: 'POST',
    });
  },

  archive(productId: string): Promise<TrainerProduct> {
    return apiRequest<TrainerProduct>(`/products/trainer/${productId}/archive/`, {
      auth: true,
      method: 'POST',
    });
  },

  remove(productId: string): Promise<void> {
    return apiRequest<void>(productPath(productId), {
      auth: true,
      method: 'DELETE',
    });
  },
};
