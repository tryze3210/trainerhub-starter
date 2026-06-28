import Link from 'next/link';

type CustomerEmptyStateProps = {
  title?: string;
  description?: string;
  actionHref?: string;
  actionLabel?: string;
};

export function CustomerEmptyState({
  title = 'Пока здесь ничего нет',
  description = 'Когда появятся данные, они будут отображаться в этом разделе.',
  actionHref = '/catalog',
  actionLabel = 'Открыть каталог',
}: CustomerEmptyStateProps) {
  return (
    <div className="customer-empty-state">
      <h3>{title}</h3>
      <p>{description}</p>
      <Link href={actionHref} className="premium-secondary-button">{actionLabel}</Link>
    </div>
  );
}
