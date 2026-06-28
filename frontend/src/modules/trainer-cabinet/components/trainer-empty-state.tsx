import Link from 'next/link';

export function TrainerEmptyState({
  title = 'Пока здесь ничего нет',
  description = 'Данные появятся после первых действий в кабинете тренера.',
  actionHref = '/trainer/dashboard/products',
  actionLabel = 'Создать продукт',
}: {
  title?: string;
  description?: string;
  actionHref?: string;
  actionLabel?: string;
}) {
  return (
    <div className="trainer-empty-state">
      <h3>{title}</h3>
      <p>{description}</p>
      <Link href={actionHref} className="premium-secondary-button">{actionLabel}</Link>
    </div>
  );
}
