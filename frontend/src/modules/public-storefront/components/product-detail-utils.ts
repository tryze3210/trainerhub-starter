import {
  getStorefrontDescription,
  getStorefrontPrice,
  type StorefrontEntityType,
  type StorefrontItem,
} from '@/modules/public-storefront/api';

export type ProductFact = {
  label: string;
  value: string;
};

export type ProductInclude = {
  title: string;
  description: string;
};

export type ProductAccessStep = {
  number: string;
  title: string;
  description: string;
};

export const PRODUCT_TYPE_LABELS: Record<StorefrontEntityType, string> = {
  video: 'Видео',
  program: 'Программа',
  bundle: 'Набор',
};

export const PRODUCT_TYPE_CONTEXT: Record<StorefrontEntityType, string> = {
  video: 'Видеоурок',
  program: 'Программа тренировок',
  bundle: 'Набор материалов',
};

export function getProductDescription(item: StorefrontItem): string {
  return getStorefrontDescription(item);
}

export function getProductPrice(item: StorefrontItem): string {
  return getStorefrontPrice(item);
}

export function getProductDuration(item: StorefrontItem): string {
  return item.duration_minutes ? `${item.duration_minutes} мин` : 'Материалы внутри';
}

export function getProductLevel(item: StorefrontItem): string {
  return item.difficulty || 'Любой уровень';
}

export function getProductCategory(item: StorefrontItem): string {
  return item.category || 'Общая подготовка';
}

export function getProductTrainer(item: StorefrontItem): string {
  return item.trainer_name || item.trainer_slug || 'TrainerHub';
}

export function buildProductFacts(item: StorefrontItem): ProductFact[] {
  return [
    { label: 'Уровень', value: getProductLevel(item) },
    { label: 'Категория', value: getProductCategory(item) },
    { label: 'Длительность', value: getProductDuration(item) },
    { label: 'Формат', value: 'Онлайн-доступ' },
    { label: 'Тренер', value: getProductTrainer(item) },
  ];
}

export function buildProductIncludes(type: StorefrontEntityType): ProductInclude[] {
  if (type === 'video') {
    return [
      { title: 'Видеоурок с понятной структурой', description: 'Материал собран так, чтобы ученик быстро понял порядок работы.' },
      { title: 'Доступ в личном кабинете', description: 'Урок открывается в кабинете после успешной оплаты.' },
      { title: 'Материалы и пояснения в одном месте', description: 'Не нужно искать ссылки и заметки в разных каналах.' },
      { title: 'Можно вернуться позже', description: 'Доступ сохраняет контекст обучения и повторного просмотра.' },
    ];
  }

  if (type === 'bundle') {
    return [
      { title: 'Несколько продуктов в одном доступе', description: 'Набор объединяет связанные материалы в один сценарий покупки.' },
      { title: 'Программы, видео или материалы', description: 'Состав зависит от продукта и отображается в личном кабинете.' },
      { title: 'Единый доступ после оплаты', description: 'Покупка активирует доступ без ручной переписки.' },
      { title: 'Удобное продолжение обучения', description: 'Ученик возвращается к материалам из кабинета.' },
    ];
  }

  return [
    { title: 'Структурная программа', description: 'Этапы помогают понимать, с чего начать и что делать дальше.' },
    { title: 'Видеоуроки и материалы', description: 'Контент собран в одном кабинете без разрозненных ссылок.' },
    { title: 'Прогресс и история прохождения', description: 'Ученик видит движение по материалам, тренер сохраняет контекст.' },
    { title: 'Доступ после успешной оплаты', description: 'Покупка открывает продукт в личном кабинете.' },
  ];
}

export const productAccessSteps: ProductAccessStep[] = [
  { number: '01', title: 'Вы покупаете доступ', description: 'Выбираете продукт и переходите к оплате.' },
  { number: '02', title: 'TrainerHub проверяет оплату', description: 'Заказ создаётся и связывается с вашим аккаунтом.' },
  { number: '03', title: 'Доступ появляется в кабинете', description: 'Материалы открываются в личном пространстве ученика.' },
  { number: '04', title: 'Обучение продолжается без ручной переписки', description: 'Уроки, материалы и прогресс остаются в системе.' },
];
