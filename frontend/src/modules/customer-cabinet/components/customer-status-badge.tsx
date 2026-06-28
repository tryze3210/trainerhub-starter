export type CustomerStatusTone = 'neutral' | 'success' | 'warning' | 'danger';

type CustomerStatusBadgeProps = {
  children: React.ReactNode;
  tone?: CustomerStatusTone;
};

export function CustomerStatusBadge({ children, tone = 'neutral' }: CustomerStatusBadgeProps) {
  return <span className={`customer-status-badge customer-status-${tone}`}>{children}</span>;
}
