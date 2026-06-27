import Link from 'next/link';

type CheckoutStateCardProps = {
  tone?: 'default' | 'error' | 'success';
  title: string;
  description: string;
  primaryHref?: string;
  primaryLabel?: string;
  secondaryHref?: string;
  secondaryLabel?: string;
};

export function CheckoutStateCard({
  tone = 'default',
  title,
  description,
  primaryHref,
  primaryLabel,
  secondaryHref,
  secondaryLabel,
}: CheckoutStateCardProps) {
  return (
    <section className={`premium-checkout-state ${tone === 'error' ? 'premium-checkout-error' : tone === 'success' ? 'premium-checkout-success' : ''}`}>
      <h1>{title}</h1>
      <p>{description}</p>
      <div className="premium-checkout-actions">
        {primaryHref && primaryLabel ? <Link href={primaryHref} className="premium-primary-button">{primaryLabel}</Link> : null}
        {secondaryHref && secondaryLabel ? <Link href={secondaryHref} className="premium-secondary-button">{secondaryLabel}</Link> : null}
      </div>
    </section>
  );
}
