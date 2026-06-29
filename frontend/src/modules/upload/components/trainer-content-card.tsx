import type { ReactNode } from 'react';

type TrainerContentCardProps = {
  active?: boolean;
  status: ReactNode;
  price: string;
  title: string;
  hasPublicAddress: boolean;
  materialsLabel: string;
  actions: ReactNode;
};

export function TrainerContentCard({
  active,
  status,
  price,
  title,
  hasPublicAddress,
  materialsLabel,
  actions,
}: TrainerContentCardProps) {
  return (
    <article className={active ? 'profile-workbench-rail-card trainer-content-rail-card trainer-content-card trainer-content-card--active trainer-content-rail-card-active trainer-content-rail-card-premium-active profile-workbench-rail-card-active' : 'profile-workbench-rail-card trainer-content-rail-card trainer-content-card'}>
      <div className="trainer-content-card-meta trainer-content-card-header">
        {status}
        <span>{price}</span>
      </div>
      <h3 className="trainer-content-card-title">{title}</h3>
      <div className="trainer-content-card-meta">
        <span>{hasPublicAddress ? 'Адрес настроен' : 'Адрес не указан'}</span>
        <span>{materialsLabel}</span>
      </div>
      <div className="trainer-content-actions trainer-content-card-actions">{actions}</div>
    </article>
  );
}
