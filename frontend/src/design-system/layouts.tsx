import type { ReactNode } from 'react';

type LayoutTone = 'public' | 'admin' | 'trainer' | 'student';

export type LayoutNavItem = {
  href: string;
  label: string;
  description?: string;
  active?: boolean;
};

function cx(...classes: Array<string | false | null | undefined>): string {
  return classes.filter(Boolean).join(' ');
}

export function DSShell({
  tone = 'public',
  sidebar,
  header,
  children,
  className,
}: {
  tone?: LayoutTone;
  sidebar?: ReactNode;
  header?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  const hasSidebar = Boolean(sidebar);
  return (
    <section className={cx('ds-layout-shell', `ds-layout-shell--${tone}`, hasSidebar && 'has-sidebar', className)}>
      {sidebar ? <aside className="ds-layout-sidebar">{sidebar}</aside> : null}
      <div className="ds-layout-main">
        {header ? <div className="ds-layout-header">{header}</div> : null}
        <div className="ds-layout-content">{children}</div>
      </div>
    </section>
  );
}

export function DSPageHeader({
  eyebrow,
  title,
  description,
  actions,
}: {
  eyebrow?: string;
  title: string;
  description?: string;
  actions?: ReactNode;
}) {
  return (
    <header className="ds-page-header">
      <div className="stack" style={{ gap: 8 }}>
        {eyebrow ? <span className="badge secondary">{eyebrow}</span> : null}
        <h1>{title}</h1>
        {description ? <p className="lead">{description}</p> : null}
      </div>
      {actions ? <div className="ds-page-header__actions">{actions}</div> : null}
    </header>
  );
}

export function DSSection({
  title,
  description,
  actions,
  children,
}: {
  title?: string;
  description?: string;
  actions?: ReactNode;
  children: ReactNode;
}) {
  return (
    <section className="ds-section">
      {title || description || actions ? (
        <div className="ds-section__header">
          <div>
            {title ? <h2 className="title-md">{title}</h2> : null}
            {description ? <p className="muted">{description}</p> : null}
          </div>
          {actions ? <div className="inline">{actions}</div> : null}
        </div>
      ) : null}
      {children}
    </section>
  );
}

export function DSLayoutNav({ items, label = 'Section navigation' }: { items: LayoutNavItem[]; label?: string }) {
  return (
    <nav className="ds-layout-nav" aria-label={label}>
      {items.map((item) => (
        <a className={cx('ds-layout-nav__item', item.active && 'is-active')} href={item.href} key={item.href}>
          <strong>{item.label}</strong>
          {item.description ? <small>{item.description}</small> : null}
        </a>
      ))}
    </nav>
  );
}

export function DSMobileActionBar({ children }: { children: ReactNode }) {
  return <div className="ds-mobile-action-bar">{children}</div>;
}

export function DSPublicLayout({ children, header }: { children: ReactNode; header?: ReactNode }) {
  return (
    <DSShell tone="public" header={header}>
      {children}
    </DSShell>
  );
}

export function DSAdminLayout({
  children,
  sidebar,
  header,
}: {
  children: ReactNode;
  sidebar: ReactNode;
  header?: ReactNode;
}) {
  return (
    <DSShell tone="admin" sidebar={sidebar} header={header}>
      {children}
    </DSShell>
  );
}

export function DSTrainerLayout({
  children,
  sidebar,
  header,
}: {
  children: ReactNode;
  sidebar: ReactNode;
  header?: ReactNode;
}) {
  return (
    <DSShell tone="trainer" sidebar={sidebar} header={header}>
      {children}
    </DSShell>
  );
}

export function DSStudentLayout({
  children,
  sidebar,
  header,
}: {
  children: ReactNode;
  sidebar?: ReactNode;
  header?: ReactNode;
}) {
  return (
    <DSShell tone="student" sidebar={sidebar} header={header}>
      {children}
    </DSShell>
  );
}
