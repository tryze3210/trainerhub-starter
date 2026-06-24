import { apiRequest } from '@/lib/api-client';

export type TrainerCRMSegment = {
  id: string;
  name: string;
  description?: string;
  color?: string;
  customers_count?: number;
};

export type TrainerCRMCustomer = {
  customer_id: string;
  profile_id: string;
  email: string;
  display_name: string;
  first_name: string;
  last_name: string;
  created_at?: string | null;
  orders_count: number;
  paid_orders_count: number;
  total_spent: string;
  period_spent: string;
  active_entitlements_count: number;
  notes_count: number;
  segments: TrainerCRMSegment[];
  last_order_at?: string | null;
  status: string;
};

export type TrainerCRMOrder = {
  id: string;
  order_type: string;
  status: string;
  currency: string;
  total_amount: string;
  created_at?: string | null;
  paid_at?: string | null;
  items_count: number;
  items: Array<{ id: string; item_type: string; title: string; total_price: string }>;
};

export type TrainerCRMAccess = {
  id: string;
  source_type: string;
  target_type: string;
  target_id?: string | null;
  status: string;
  starts_at?: string | null;
  ends_at?: string | null;
  created_at?: string | null;
};

export type TrainerCRMAttendance = {
  id: string;
  status: string;
  title: string;
  notes: string;
  starts_at?: string | null;
  ends_at?: string | null;
  created_at?: string | null;
};

export type TrainerCRMNote = {
  id: string;
  body: string;
  visibility: string;
  pinned: boolean;
  created_at?: string | null;
  updated_at?: string | null;
};

export type TrainerCRMSnapshot = {
  summary: {
    customers_count: number;
    with_active_access_count: number;
    with_notes_count: number;
    segments_count: number;
    period_days: number;
  };
  segments: TrainerCRMSegment[];
  items: TrainerCRMCustomer[];
};

export type TrainerCRMDetail = {
  customer: TrainerCRMCustomer;
  purchase_history: TrainerCRMOrder[];
  access_history: TrainerCRMAccess[];
  attendance_history: TrainerCRMAttendance[];
  notes: TrainerCRMNote[];
  segments: TrainerCRMSegment[];
};

export const trainerCrmApi = {
  getSnapshot(days = 90, search = '') {
    const params = new URLSearchParams({ days: String(days), limit: '100' });
    if (search.trim()) params.set('search', search.trim());
    return apiRequest<TrainerCRMSnapshot>(`/customer/trainer-crm/?${params.toString()}`, { auth: true });
  },

  getCustomer(customerId: string) {
    return apiRequest<TrainerCRMDetail>(`/customer/trainer-crm/${customerId}/`, { auth: true });
  },

  createNote(customerId: string, body: string, pinned = false) {
    return apiRequest<TrainerCRMNote>('/customer/trainer-crm/notes/', {
      auth: true,
      method: 'POST',
      body: JSON.stringify({ customer_id: customerId, body, pinned }),
    });
  },

  createSegment(name: string, description = '', color = '') {
    return apiRequest<TrainerCRMSegment>('/customer/trainer-crm/segments/', {
      auth: true,
      method: 'POST',
      body: JSON.stringify({ name, description, color }),
    });
  },

  assignSegment(customerId: string, segmentId: string) {
    return apiRequest<{ assigned: boolean }>('/customer/trainer-crm/segments/assign/', {
      auth: true,
      method: 'POST',
      body: JSON.stringify({ customer_id: customerId, segment_id: segmentId }),
    });
  },
};
