export type TrainerMetric = {
  label: string;
  value: string | number;
  hint?: string;
  tone?: 'neutral' | 'success' | 'warning' | 'danger' | 'primary';
};

export function TrainerMetricCard({ metric }: { metric: TrainerMetric }) {
  return (
    <article className={`trainer-metric-card trainer-metric-card-${metric.tone || 'neutral'}`}>
      <span>{metric.label}</span>
      <strong>{metric.value}</strong>
      {metric.hint ? <small>{metric.hint}</small> : null}
    </article>
  );
}
