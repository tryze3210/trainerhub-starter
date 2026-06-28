export type TrainerStatusTone = 'neutral' | 'success' | 'warning' | 'danger' | 'primary';

export function TrainerStatusBadge({ children, tone = 'neutral' }: { children: React.ReactNode; tone?: TrainerStatusTone }) {
  return <span className={`trainer-status-badge trainer-status-${tone}`}>{children}</span>;
}
