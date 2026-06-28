type CustomerDashboardCardProps = {
  title: string;
  children: React.ReactNode;
  action?: React.ReactNode;
};

export function CustomerDashboardCard({ title, children, action }: CustomerDashboardCardProps) {
  return (
    <section className="customer-dashboard-card">
      <div className="customer-section-header">
        <h2>{title}</h2>
        {action}
      </div>
      {children}
    </section>
  );
}
