type CheckoutOrderSummaryProps = {
  title: string;
  itemType: string;
  amount: string;
  currency: string;
};

const itemTypeLabels: Record<string, string> = {
  video: 'Видеоурок',
  program: 'Программа',
  bundle: 'Набор материалов',
  subscription: 'Подписка',
};

export function formatCheckoutPrice(amount: string, currency: string) {
  const numeric = Number(amount);
  if (!Number.isFinite(numeric)) return `${amount || '0'} ${currency || 'RUB'}`;

  return new Intl.NumberFormat('ru-RU', {
    style: 'currency',
    currency: currency || 'RUB',
    maximumFractionDigits: numeric % 1 === 0 ? 0 : 2,
  }).format(numeric);
}

export function itemTypeLabel(itemType: string) {
  return itemTypeLabels[itemType] || 'Цифровой продукт';
}

export function CheckoutOrderSummary({ title, itemType, amount, currency }: CheckoutOrderSummaryProps) {
  return (
    <section className="premium-checkout-summary" aria-label="Состав заказа">
      <div className="premium-checkout-row">
        <span>Продукт</span>
        <strong>{title || 'Выбранный продукт'}</strong>
      </div>
      <div className="premium-checkout-row">
        <span>Тип</span>
        <strong>{itemTypeLabel(itemType)}</strong>
      </div>
      <div className="premium-checkout-row">
        <span>Стоимость</span>
        <strong>{formatCheckoutPrice(amount, currency)}</strong>
      </div>
      <div className="premium-checkout-row">
        <span>Валюта</span>
        <strong>{currency || 'RUB'}</strong>
      </div>
      <div className="premium-checkout-row">
        <span>Доступ после оплаты</span>
        <strong>Автоматически в личном кабинете</strong>
      </div>
    </section>
  );
}
