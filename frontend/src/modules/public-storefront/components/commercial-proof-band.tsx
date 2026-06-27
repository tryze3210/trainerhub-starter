import { AnimatedMetric, AnimatedSection } from '@/design-system';

type MetricItem = {
  value: string;
  label: string;
};

const metrics: MetricItem[] = [
  { value: '8', label: 'модулей в одной платформе' },
  { value: '3', label: 'рабочих пространства: тренер, ученик, администратор' },
  { value: '24/7', label: 'доступ к купленным материалам' },
  { value: '1', label: 'система вместо чатов, таблиц и ручных оплат' },
];

export function CommercialProofBand() {
  return (
    <AnimatedSection className="premium-section" aria-labelledby="commercial-proof-title">
      <div className="premium-proof-band">
        <div className="premium-section-header">
          <span className="premium-eyebrow">COMMERCIAL PROOF</span>
          <h2 className="premium-section-title" id="commercial-proof-title">
            Честная операционная основа без громких обещаний
          </h2>
        </div>

        <div className="premium-proof-band__metrics">
          {metrics.map((metric, index) => (
            <AnimatedMetric className="premium-metric-card" delayMs={index * 100} key={metric.label}>
              <strong>{metric.value}</strong>
              <span>{metric.label}</span>
            </AnimatedMetric>
          ))}
        </div>
      </div>
    </AnimatedSection>
  );
}
