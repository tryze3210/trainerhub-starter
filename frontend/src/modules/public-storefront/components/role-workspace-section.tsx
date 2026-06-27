import { AnimatedCard, AnimatedSection } from '@/design-system';

type RolePanel = {
  title: string;
  description: string;
  features: string[];
  metric: string;
  metricLabel: string;
};

const panels: RolePanel[] = [
  {
    title: 'Для тренера',
    description: 'Создавайте программы, продавайте доступы, ведите учеников и видите выручку в одном кабинете.',
    features: ['Каталог продуктов', 'CRM и заметки по клиентам', 'Расписание и посещаемость', 'Продажи, выплаты и аналитика'],
    metric: '31',
    metricLabel: 'покупка программ за месяц',
  },
  {
    title: 'Для ученика',
    description: 'Покупайте программы, смотрите уроки, отслеживайте прогресс и продолжайте обучение без поиска ссылок.',
    features: ['Купленные курсы', 'Прогресс уроков', 'Материалы и задания', 'Сообщения от тренера'],
    metric: '82%',
    metricLabel: 'прогресс активной программы',
  },
  {
    title: 'Для администратора',
    description: 'Контролируйте платежи, возвраты, выплаты, поддержку, аудит и финансовые операции.',
    features: ['Платёжные статусы', 'Refund и disputes', 'Payout контроль', 'Audit и support console'],
    metric: '1',
    metricLabel: 'операционная система для контроля',
  },
];

export function RoleWorkspaceSection() {
  return (
    <AnimatedSection className="premium-section" aria-labelledby="role-workspace-title">
      <div className="premium-section-header">
        <span className="premium-eyebrow">WORKSPACES</span>
        <h2 className="premium-section-title" id="role-workspace-title">
          Три рабочих пространства вокруг одного коммерческого продукта
        </h2>
      </div>

      <div className="premium-role-grid">
        {panels.map((panel, index) => (
          <AnimatedCard className="premium-role-card" delayMs={index * 120} key={panel.title}>
            <div>
              <span className="premium-eyebrow">{panel.title}</span>
              <h3>{panel.description}</h3>
            </div>
            <ul>
              {panel.features.map((feature) => (
                <li key={feature}>{feature}</li>
              ))}
            </ul>
            <div className="premium-role-card__metric">
              <strong>{panel.metric}</strong>
              <span>{panel.metricLabel}</span>
            </div>
          </AnimatedCard>
        ))}
      </div>
    </AnimatedSection>
  );
}
