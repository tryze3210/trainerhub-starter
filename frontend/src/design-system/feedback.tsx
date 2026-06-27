import type { HTMLAttributes, ReactNode } from 'react';

import { DSButton } from './components';

type FeedbackTone = 'neutral' | 'success' | 'warning' | 'danger' | 'primary';
type LiveState = 'connected' | 'connecting' | 'offline' | 'error';

function cx(...classes: Array<string | false | null | undefined>): string {
  return classes.filter(Boolean).join(' ');
}

export type DSNotificationFeedItem = {
  id: string;
  title: string;
  description?: string;
  timestamp?: string;
  tone?: FeedbackTone;
  unread?: boolean;
  action?: ReactNode;
};

export type DSPresenceUser = {
  id: string;
  name: string;
  initials: string;
  status?: 'online' | 'away' | 'offline';
};

export type DSActivityTimelineItem = {
  id: string;
  actor: string;
  action: string;
  target?: string;
  timestamp?: string;
  tone?: FeedbackTone;
};

export function DSSkeleton({
  lines = 1,
  className,
}: {
  lines?: number;
  className?: string;
}) {
  return (
    <div className={cx('ds-skeleton-stack', className)} aria-hidden="true">
      {Array.from({ length: lines }, (_, index) => (
        <span className="skeleton" key={index} />
      ))}
    </div>
  );
}

export function DSEmptyState({
  title,
  description,
  action,
  tone = 'neutral',
}: {
  title: string;
  description?: string;
  action?: ReactNode;
  tone?: FeedbackTone;
}) {
  return (
    <section className={cx('empty-state', 'ds-empty-state', tone !== 'neutral' && `ds-empty-state--${tone}`)}>
      <span className="ds-empty-state__mark" aria-hidden="true" />
      <div>
        <h2 className="title-md">{title}</h2>
        {description ? <p>{description}</p> : null}
      </div>
      {action ? <div className="inline">{action}</div> : null}
    </section>
  );
}

export function DSToast({
  title,
  description,
  tone = 'neutral',
  actionLabel,
  onAction,
}: {
  title: string;
  description?: string;
  tone?: FeedbackTone;
  actionLabel?: string;
  onAction?: () => void;
}) {
  return (
    <section className={cx('ds-toast', tone !== 'neutral' && `ds-toast--${tone}`)} role="status" aria-live="polite">
      <span className="ds-status-dot" aria-hidden="true" />
      <div>
        <strong>{title}</strong>
        {description ? <p>{description}</p> : null}
      </div>
      {actionLabel && onAction ? (
        <DSButton size="sm" variant="ghost" type="button" onClick={onAction}>
          {actionLabel}
        </DSButton>
      ) : null}
    </section>
  );
}

export function DSToastStack({ children }: { children: ReactNode }) {
  return <div className="ds-toast-stack">{children}</div>;
}

export function DSLiveIndicator({
  state = 'connected',
  label,
  updatedAt,
}: {
  state?: LiveState;
  label?: string;
  updatedAt?: string;
}) {
  const textByState: Record<LiveState, string> = {
    connected: 'Live',
    connecting: 'Connecting',
    offline: 'Offline',
    error: 'Sync issue',
  };

  return (
    <span className={cx('ds-live-indicator', `ds-live-indicator--${state}`)} role="status" aria-live="polite">
      <span className="ds-live-indicator__pulse" aria-hidden="true" />
      <span>{label ?? textByState[state]}</span>
      {updatedAt ? <small>{updatedAt}</small> : null}
    </span>
  );
}

export function DSNotificationFeed({
  items,
  emptyTitle = 'No live updates',
}: {
  items: DSNotificationFeedItem[];
  emptyTitle?: string;
}) {
  if (items.length === 0) {
    return <DSEmptyState title={emptyTitle} tone="neutral" />;
  }

  return (
    <section className="ds-notification-feed" aria-live="polite">
      {items.map((item) => (
        <article
          className={cx(
            'ds-notification-feed__item',
            item.unread && 'ds-notification-feed__item--unread',
            item.tone && item.tone !== 'neutral' && `ds-notification-feed__item--${item.tone}`,
          )}
          key={item.id}
        >
          <span className="ds-status-dot" aria-hidden="true" />
          <div>
            <strong>{item.title}</strong>
            {item.description ? <p>{item.description}</p> : null}
            {item.timestamp ? <small>{item.timestamp}</small> : null}
          </div>
          {item.action ? <div className="ds-notification-feed__action">{item.action}</div> : null}
        </article>
      ))}
    </section>
  );
}

export function DSPresenceStack({
  users,
  maxVisible = 4,
  label = 'Active collaborators',
}: {
  users: DSPresenceUser[];
  maxVisible?: number;
  label?: string;
}) {
  const visibleUsers = users.slice(0, maxVisible);
  const hiddenCount = Math.max(users.length - visibleUsers.length, 0);

  return (
    <div className="ds-presence-stack" aria-label={label}>
      <div className="ds-presence-stack__avatars">
        {visibleUsers.map((user) => (
          <span
            className={cx('ds-presence-stack__avatar', `ds-presence-stack__avatar--${user.status ?? 'online'}`)}
            key={user.id}
            title={user.name}
          >
            {user.initials}
          </span>
        ))}
        {hiddenCount > 0 ? <span className="ds-presence-stack__more">+{hiddenCount}</span> : null}
      </div>
      <span>{users.length} active</span>
    </div>
  );
}

export function DSActivityTimeline({
  items,
  emptyTitle = 'No activity yet',
}: {
  items: DSActivityTimelineItem[];
  emptyTitle?: string;
}) {
  if (items.length === 0) {
    return <DSEmptyState title={emptyTitle} tone="neutral" />;
  }

  return (
    <section className="ds-activity-timeline" aria-label="Activity timeline">
      {items.map((item) => (
        <article
          className={cx('ds-activity-timeline__item', item.tone && item.tone !== 'neutral' && `ds-activity-timeline__item--${item.tone}`)}
          key={item.id}
        >
          <span className="ds-status-dot" aria-hidden="true" />
          <div>
            <p>
              <strong>{item.actor}</strong> {item.action}
              {item.target ? <span> {item.target}</span> : null}
            </p>
            {item.timestamp ? <small>{item.timestamp}</small> : null}
          </div>
        </article>
      ))}
    </section>
  );
}

export function DSTransitionPanel({
  active = true,
  className,
  children,
  ...props
}: HTMLAttributes<HTMLElement> & {
  active?: boolean;
  children: ReactNode;
}) {
  return (
    <section className={cx('ds-transition-panel', active && 'is-active', className)} {...props}>
      {children}
    </section>
  );
}

export function DSStatusDot({
  tone = 'neutral',
  label,
}: {
  tone?: FeedbackTone;
  label?: string;
}) {
  return (
    <span className={cx('ds-status', tone !== 'neutral' && `ds-status--${tone}`)}>
      <span className="ds-status-dot" aria-hidden="true" />
      {label ? <span>{label}</span> : null}
    </span>
  );
}
