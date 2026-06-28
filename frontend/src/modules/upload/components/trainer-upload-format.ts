export type TrainerContentTab = 'videos' | 'programs' | 'bundles';

export type TrainerContentStatusTone =
  | 'neutral'
  | 'success'
  | 'warning'
  | 'danger';

export function makeTrainerContentSlug(value: string) {
  return value
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9а-яё\s-]/gi, '')
    .replace(/\s+/g, '-')
    .replace(/-+/g, '-');
}

export function trainerContentStatusLabel(status?: string) {
  switch (status) {
    case 'published':
      return 'Опубликовано';
    case 'submitted':
      return 'Отправлено на проверку';
    case 'review':
    case 'under_review':
      return 'На проверке';
    case 'archived':
      return 'В архиве';
    default:
      return 'Черновик';
  }
}

export function trainerContentStatusTone(status?: string): TrainerContentStatusTone {
  switch (status) {
    case 'published':
      return 'success';
    case 'review':
    case 'submitted':
    case 'under_review':
      return 'warning';
    case 'rejected':
      return 'danger';
    default:
      return 'neutral';
  }
}

export function trainerContentEntityLabel(tab: TrainerContentTab) {
  if (tab === 'videos') return 'видео';
  if (tab === 'programs') return 'программа';
  return 'набор';
}

export function trainerContentPrice(value?: string, currency?: string) {
  const number = Number(value || 0);
  if (!Number.isFinite(number) || number <= 0) return 'Бесплатно';
  return new Intl.NumberFormat('ru-RU', {
    style: 'currency',
    currency: currency || 'RUB',
    maximumFractionDigits: 2,
  }).format(number);
}

export function trainerContentFileSize(bytes?: number) {
  if (!bytes || !Number.isFinite(bytes)) return '0 МБ';
  const megabytes = bytes / 1024 / 1024;
  if (megabytes < 1024) return `${megabytes.toFixed(1)} МБ`;
  return `${(megabytes / 1024).toFixed(2)} ГБ`;
}
