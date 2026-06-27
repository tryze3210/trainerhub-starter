export type CheckoutProvider = 'mock' | 'cloudpayments' | 'yookassa';

const providers: { value: CheckoutProvider; label: string; description: string }[] = [
  {
    value: 'mock',
    label: 'Тестовая оплата',
    description: 'Подходит для локальной проверки покупки.',
  },
  {
    value: 'cloudpayments',
    label: 'CloudPayments',
    description: 'Создаёт платёжную сессию у провайдера.',
  },
  {
    value: 'yookassa',
    label: 'ЮKassa',
    description: 'Создаёт платёжную сессию у провайдера.',
  },
];

type CheckoutPaymentMethodProps = {
  provider: CheckoutProvider;
  onProviderChange: (provider: CheckoutProvider) => void;
};

export function CheckoutPaymentMethod({ provider, onProviderChange }: CheckoutPaymentMethodProps) {
  return (
    <div className="premium-checkout-provider" role="radiogroup" aria-label="Способ оплаты">
      {providers.map((item) => (
        <label key={item.value} className={provider === item.value ? 'premium-checkout-provider-active' : ''}>
          <input
            type="radio"
            name="checkout-provider"
            value={item.value}
            checked={provider === item.value}
            onChange={() => onProviderChange(item.value)}
          />
          <span>
            <strong>{item.label}</strong>
            <small>{item.description}</small>
          </span>
        </label>
      ))}
    </div>
  );
}
