export type CustomerAction = {
  label: string;
  href: string;
  variant?: 'primary' | 'secondary';
};

type CustomerSectionHeaderProps = {
  title: string;
  description?: string;
  children?: React.ReactNode;
};

export function CustomerSectionHeader({ title, description, children }: CustomerSectionHeaderProps) {
  return (
    <div className="customer-section-header">
      <div>
        <h2>{title}</h2>
        {description ? <p>{description}</p> : null}
      </div>
      {children}
    </div>
  );
}
