import type { Entitlement, Order, Payment, Subscription } from '@/types/api';

export function formatCustomerDate(value?: string | null): string {
  if (!value) return 'Нет данных';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat('ru-RU', { dateStyle: 'medium' }).format(date);
}

export function formatCustomerMoney(value?: string | number | null, currency = 'RUB'): string {
  if (value === undefined || value === null || value === '') return `0 ${currency}`;
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return `${value} ${currency}`;
  return new Intl.NumberFormat('ru-RU', {
    style: 'currency',
    currency,
    maximumFractionDigits: numeric % 1 === 0 ? 0 : 2,
  }).format(numeric);
}

export function shortCustomerNumber(value?: string | null, prefix = 'TH'): string {
  if (!value) return `${prefix}-0000`;
  return `${prefix}-${value.replaceAll('-', '').slice(-6).toUpperCase()}`;
}

export function orderTitle(order: Order): string {
  return order.title || order.items?.[0]?.title_snapshot || 'Покупка TrainerHub';
}

export function orderAmount(order: Order): string {
  return formatCustomerMoney(order.total_amount || order.gross_amount || order.amount, order.currency || 'RUB');
}

export function orderStatusLabel(status?: string): string {
  const value = (status || '').toLowerCase();
  if (value === 'paid' || value === 'completed') return 'Оплачен';
  if (value === 'pending' || value === 'awaiting_payment' || value === 'created') return 'Ожидает оплаты';
  if (value === 'failed') return 'Ошибка оплаты';
  if (value === 'cancelled' || value === 'canceled') return 'Отменён';
  if (value === 'refunded') return 'Возвращён';
  return status || 'Нет данных';
}

export function paymentStatusLabel(status?: string): string {
  const value = (status || '').toLowerCase();
  if (value === 'succeeded' || value === 'paid' || value === 'completed') return 'Успешно';
  if (value === 'pending' || value === 'created') return 'В ожидании';
  if (value === 'failed') return 'Не прошёл';
  if (value === 'cancelled' || value === 'canceled') return 'Отменён';
  if (value === 'refunded') return 'Возврат';
  return status || 'Нет данных';
}

export function subscriptionStatusLabel(status?: string): string {
  const value = (status || '').toLowerCase();
  if (value === 'trial' || value === 'trialing') return 'Пробный период';
  if (value === 'active') return 'Активна';
  if (value === 'pending') return 'Ожидает оплаты';
  if (value === 'past_due') return 'Требуется оплата';
  if (value === 'cancelled' || value === 'canceled') return 'Отменена';
  if (value === 'expired') return 'Истекла';
  return status || 'Нет данных';
}

export function accessTypeLabel(value?: string): string {
  const normalized = (value || '').toLowerCase();
  if (normalized === 'video') return 'Видео';
  if (normalized === 'program') return 'Программа';
  if (normalized === 'bundle') return 'Набор';
  if (normalized === 'subscription') return 'Подписка';
  if (normalized === 'one_time') return 'Разовый доступ';
  if (normalized === 'course') return 'Курс';
  return value || 'Доступ';
}

export function accessStatusLabel(status?: string, active?: boolean): string {
  const value = (status || '').toLowerCase();
  if (value === 'active' || value === 'granted' || active) return 'Активен';
  if (value === 'pending') return 'Ожидает активации';
  if (value === 'expired') return 'Истёк';
  if (value === 'revoked') return 'Отозван';
  if (value === 'inactive') return 'Неактивен';
  return status || 'Нет данных';
}

export function statusTone(status?: string, active?: boolean): 'neutral' | 'success' | 'warning' | 'danger' {
  const value = (status || '').toLowerCase();
  if (active || ['active', 'granted', 'paid', 'completed', 'succeeded'].includes(value)) return 'success';
  if (['pending', 'created', 'awaiting_payment', 'past_due'].includes(value)) return 'warning';
  if (['failed', 'cancelled', 'canceled', 'expired', 'revoked', 'inactive', 'refunded'].includes(value)) return 'danger';
  return 'neutral';
}

export function entitlementTitle(item: Entitlement): string {
  return item.content_title || item.title || item.product_title || accessTypeLabel(item.target_type || item.kind);
}

export function entitlementType(item: Entitlement): string {
  return accessTypeLabel(item.access_kind || item.entitlement_type || item.content_type || item.target_type || item.kind);
}

export function entitlementStatus(item: Entitlement): string {
  return item.status || item.access_status || (item.is_active ? 'active' : 'inactive');
}

export function subscriptionTitle(item: Subscription): string {
  return item.plan?.title || item.plan_name || item.title || item.product_title || 'Подписка';
}

export function paymentTitle(item: Payment): string {
  return item.order_reference || shortCustomerNumber(item.order_id || item.id, 'PAY');
}
