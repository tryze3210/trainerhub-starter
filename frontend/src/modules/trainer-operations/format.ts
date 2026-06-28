export type TrainerOperationStatusTone = 'success' | 'warning' | 'danger' | 'neutral';

export function trainerOperationStatusLabel(value?: string | null): string {
  const status = (value || '').toLowerCase();

  if (status === 'active') return 'Активен';
  if (status === 'inactive') return 'Неактивен';
  if (status === 'open') return 'Свободно';
  if (status === 'booked') return 'Забронировано';
  if (status === 'confirmed') return 'Подтверждено';
  if (status === 'cancelled') return 'Отменено';
  if (status === 'checked_in') return 'На занятии';
  if (status === 'attended') return 'Посещение завершено';
  if (status === 'no_show') return 'Не пришёл';
  if (status === 'waiting') return 'Ожидает';
  if (status === 'draft') return 'Черновик';
  if (status === 'paid') return 'Оплачено';
  if (status === 'refunded') return 'Возвращено';
  if (status === 'expired') return 'Истёк';
  if (status === 'pending') return 'Ожидает';

  return 'Требуется проверка';
}

export function trainerOperationStatusTone(value?: string | null): TrainerOperationStatusTone {
  const status = (value || '').toLowerCase();

  if (['active', 'open', 'confirmed', 'attended', 'paid'].includes(status)) return 'success';
  if (['booked', 'checked_in', 'waiting', 'pending', 'draft'].includes(status)) return 'warning';
  if (['cancelled', 'no_show', 'inactive', 'refunded', 'expired'].includes(status)) return 'danger';

  return 'neutral';
}
