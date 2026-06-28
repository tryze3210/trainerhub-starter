export type CustomerMetric = {
  label: string;
  value: string | number;
  hint?: string;
  tone?: 'neutral' | 'success' | 'warning' | 'danger';
};

export function CustomerMetricCard({ metric }: { metric: CustomerMetric }) {
  return (
    <article className={`customer-metric-card customer-metric-card-${metric.tone || 'neutral'}`}>
      <span>{metric.label}</span>
      <strong>{metric.value}</strong>
      {metric.hint ? <small>{metric.hint}</small> : null}
    </article>
  );
}
