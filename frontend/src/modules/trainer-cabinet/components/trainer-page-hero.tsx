export function TrainerPageHero({ title, description, actions }: { title: string; description: string; actions?: React.ReactNode }) {
  return (
    <section className="trainer-page-hero">
      <div>
        <span className="premium-eyebrow">Кабинет тренера</span>
        <h1 className="trainer-page-title">{title}</h1>
        <p className="trainer-page-subtitle">{description}</p>
      </div>
      {actions ? <div className="trainer-page-actions">{actions}</div> : null}
    </section>
  );
}
