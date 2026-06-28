export type TrainerAction = {
  label: string;
  href: string;
  variant?: 'primary' | 'secondary';
};

export function TrainerSectionHeader({ title, description, children }: { title: string; description?: string; children?: React.ReactNode }) {
  return (
    <div className="trainer-section-header">
      <div>
        <h2>{title}</h2>
        {description ? <p>{description}</p> : null}
      </div>
      {children}
    </div>
  );
}
