import type { ReactNode } from 'react';
import Link from 'next/link';

export type ProfileWorkbenchTone = 'customer' | 'trainer' | 'admin';

export type ProfileWorkbenchNavItem = {
  href: string;
  label: string;
  description?: string;
};

export type ProfileWorkbenchMetricData = {
  label: string;
  value: string | number;
  hint?: string;
  tone?: 'neutral' | 'success' | 'warning' | 'danger' | 'primary';
};

export function ProfileWorkbench({ tone, children }: { tone: ProfileWorkbenchTone; children: ReactNode }) {
  return <section className={`profile-workbench profile-workbench-${tone}`}>{children}</section>;
}

export function ProfileWorkbenchHero({
  eyebrow,
  title,
  description,
  actions,
}: {
  eyebrow: string;
  title: string;
  description: string;
  actions?: ReactNode;
}) {
  return (
    <header className="profile-workbench-hero">
      <div className="profile-workbench-hero-copy">
        <p className="premium-eyebrow">{eyebrow}</p>
        <h1>{title}</h1>
        <p>{description}</p>
      </div>
      {actions ? <div className="profile-workbench-hero-actions">{actions}</div> : null}
    </header>
  );
}

export function ProfileWorkbenchNav({
  items,
  activeHref,
  showDescriptions = false,
}: {
  items: ProfileWorkbenchNavItem[];
  activeHref?: string;
  showDescriptions?: boolean;
}) {
  return (
    <nav className="profile-workbench-nav" aria-label="Разделы профиля">
      {items.map((item) => {
        const active = activeHref === item.href || Boolean(activeHref?.startsWith(`${item.href}/`));
        return (
          <Link key={`${item.href}-${item.label}`} href={item.href} className={active ? 'profile-workbench-nav-link profile-workbench-nav-link-active' : 'profile-workbench-nav-link'} aria-current={active ? 'page' : undefined}>
            <strong>{item.label}</strong>
            {showDescriptions && item.description ? <span>{item.description}</span> : null}
          </Link>
        );
      })}
    </nav>
  );
}

export function ProfileWorkbenchMetrics({ children }: { children: ReactNode }) {
  return <section className="profile-workbench-metrics">{children}</section>;
}

export function ProfileWorkbenchMetric({ metric }: { metric: ProfileWorkbenchMetricData }) {
  return (
    <article className={`profile-workbench-metric profile-workbench-metric-${metric.tone || 'neutral'}`}>
      <span>{metric.label}</span>
      <strong>{metric.value}</strong>
      {metric.hint ? <small>{metric.hint}</small> : null}
    </article>
  );
}

export function ProfileWorkbenchRail({ children }: { children: ReactNode }) {
  return <div className="profile-workbench-rail">{children}</div>;
}

export function ProfileWorkbenchRailCard({ active, children }: { active?: boolean; children: ReactNode }) {
  return <article className={active ? 'profile-workbench-rail-card profile-workbench-rail-card-active' : 'profile-workbench-rail-card'}>{children}</article>;
}

export function ProfileWorkbenchPanel({ children }: { children: ReactNode }) {
  return <article className="profile-workbench-panel">{children}</article>;
}

export function ProfileWorkbenchEditorPanel({ children }: { children: ReactNode }) {
  return <section className="profile-workbench-editor-panel">{children}</section>;
}

export function ProfileWorkbenchSupportPanels({ children }: { children: ReactNode }) {
  return <section className="profile-workbench-support-panels">{children}</section>;
}

export function ProfileWorkbenchSectionHeader({ title, description, actions }: { title: string; description?: string; actions?: ReactNode }) {
  return (
    <header className="profile-workbench-section-header">
      <div>
        <h2>{title}</h2>
        {description ? <p>{description}</p> : null}
      </div>
      {actions ? <div className="profile-workbench-actions">{actions}</div> : null}
    </header>
  );
}
