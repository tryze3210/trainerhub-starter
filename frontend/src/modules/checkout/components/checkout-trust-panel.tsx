const trustItems = [
  'Доступ активируется после успешной оплаты.',
  'Покупка привязана к вашему аккаунту.',
  'Заказ и платёж можно будет открыть в личном кабинете.',
];

export function CheckoutTrustPanel() {
  return (
    <section className="premium-checkout-trust" aria-label="Условия доступа">
      {trustItems.map((item) => (
        <div key={item}>{item}</div>
      ))}
    </section>
  );
}
