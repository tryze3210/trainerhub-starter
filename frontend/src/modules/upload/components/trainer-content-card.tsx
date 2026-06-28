import type { ReactNode } from 'react';

type TrainerContentCardProps = {
  active?: boolean;
  status: ReactNode;
  price: string;
  title: string;
  description: string;
  publicAddress: string;
  materialsLabel: string;
  actions: ReactNode;
};

export function TrainerContentCard({
  active,
  status,
  price,
  title,
  description,
  publicAddress,
  materialsLabel,
  actions,
}: TrainerContentCardProps) {
  return (
    <article className={active ? 'trainer-content-card trainer-content-card-active' : 'trainer-content-card'}>
      <div className="trainer-content-card-meta">
        {status}
        <span>{price}</span>
      </div>
      <h3>{title}</h3>
      <p>{description}</p>
      <div className="trainer-content-card-meta">
        <span>Публичный адрес: {publicAddress || 'не указан'}</span>
        <span>{materialsLabel}</span>
      </div>
      <div className="trainer-content-actions">{actions}</div>
    </article>
  );
}
