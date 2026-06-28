export function formatTrainerMoney(value?: string | number | null, currency = 'RUB'): string {
  if (value === undefined || value === null || value === '') return `0 ${currency}`;
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return `${value} ${currency}`;
  return new Intl.NumberFormat('ru-RU', {
    style: 'currency',
    currency,
    maximumFractionDigits: numeric % 1 === 0 ? 0 : 2,
  }).format(numeric);
}

export function formatTrainerDate(value?: string | null): string {
  if (!value) return 'Нет данных';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat('ru-RU', { dateStyle: 'medium' }).format(date);
}

export function trainerStatusLabel(status?: string): string {
  const value = (status || '').toLowerCase();
  if (value === 'draft') return 'Черновик';
  if (value === 'published') return 'Опубликован';
  if (value === 'pending_review') return 'На проверке';
  if (value === 'approved') return 'Одобрено';
  if (value === 'rejected') return 'Отклонено';
  if (value === 'paid') return 'Оплачен';
  if (value === 'pending') return 'В ожидании';
  if (value === 'failed') return 'Не прошёл';
  if (value === 'active') return 'Активен';
  if (value === 'blocked') return 'Заблокировано';
  if (value === 'healthy' || value === 'ok' || value === 'ready' || value === 'done') return 'В норме';
  if (value === 'warning' || value === 'attention' || value === 'changes_requested' || value === 'under_review') return 'Требует внимания';
  if (value === 'critical' || value === 'blocker') return 'Критично';
  return status || 'Нет данных';
}

export function trainerStatusTone(status?: string): 'neutral' | 'success' | 'warning' | 'danger' | 'primary' {
  const value = (status || '').toLowerCase();
  if (['published', 'approved', 'paid', 'active', 'healthy', 'ok', 'ready', 'done', 'success'].includes(value)) return 'success';
  if (['pending', 'pending_review', 'warning', 'attention', 'changes_requested', 'under_review'].includes(value)) return 'warning';
  if (['failed', 'blocked', 'critical', 'blocker', 'rejected'].includes(value)) return 'danger';
  if (['draft', 'created'].includes(value)) return 'neutral';
  return 'neutral';
}

export function trainerProductTypeLabel(value?: string): string {
  const type = (value || '').toLowerCase();
  if (type === 'video') return 'Видео';
  if (type === 'program') return 'Программа';
  if (type === 'bundle') return 'Набор';
  if (type === 'course') return 'Курс';
  return value || 'Продукт';
}

export function trainerPayoutStatusLabel(status?: string): string {
  return trainerStatusLabel(status);
}

export function trainerOrderStatusLabel(status?: string): string {
  return trainerStatusLabel(status);
}
