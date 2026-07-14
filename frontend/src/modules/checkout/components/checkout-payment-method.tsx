export type CheckoutProvider = 'mock' | 'cloudpayments' | 'yookassa';

export type CheckoutProviderOption = {
  value: CheckoutProvider;
  label: string;
  description: string;
};

const providerDescriptions: Record<CheckoutProvider, string> = {
  mock: 'Подходит только для локальной проверки покупки.',
  cloudpayments: 'Безопасная оплата банковской картой.',
  yookassa: 'Оплата картой или через доступные способы ЮKassa.',
};

type CheckoutPaymentMethodProps = {
  provider: CheckoutProvider | '';
  providers: CheckoutProviderOption[];
  onProviderChange: (provider: CheckoutProvider) => void;
};

export function toCheckoutProviderOption(provider: string, label?: string): CheckoutProviderOption | null {
  if (provider !== 'mock' && provider !== 'cloudpayments' && provider !== 'yookassa') {
    return null;
  }

  return {
    value: provider,
    label: label || provider,
    description: providerDescriptions[provider],
  };
}

export function CheckoutPaymentMethod({ provider, providers, onProviderChange }: CheckoutPaymentMethodProps) {
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
