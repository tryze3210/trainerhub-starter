import type {
  ChangeEventHandler,
  HTMLAttributes,
  InputHTMLAttributes,
  ReactNode,
  TextareaHTMLAttributes,
  VideoHTMLAttributes,
} from 'react';

import { DSButton, DSCard, DSDataTable, DSStatCard } from './components';

type Tone = 'primary' | 'success' | 'warning' | 'danger' | 'neutral';

function cx(...classes: Array<string | false | null | undefined>): string {
  return classes.filter(Boolean).join(' ');
}

export type DSChartDatum = {
  label: string;
  value: number;
  tone?: Tone;
};

export function DSBarChart({
  data,
  maxValue,
  label,
}: {
  data: DSChartDatum[];
  maxValue?: number;
  label?: string;
}) {
  const highest = Math.max(maxValue ?? 0, ...data.map((item) => item.value), 1);

  return (
    <div className="ds-chart" role="img" aria-label={label ?? 'Bar chart'}>
      {data.map((item) => {
        const width = Math.max(4, Math.round((item.value / highest) * 100));
        return (
          <div className="ds-chart__row" key={item.label}>
            <span>{item.label}</span>
            <div className="ds-chart__track">
              <div
                className={cx('ds-chart__bar', item.tone && `ds-chart__bar--${item.tone}`)}
                style={{ width: `${width}%` }}
              />
            </div>
            <strong>{item.value}</strong>
          </div>
        );
      })}
    </div>
  );
}

export type DSCalendarEvent = {
  id: string;
  day: number;
  title: string;
  tone?: Tone;
};

export function DSCalendar({
  monthLabel,
  days,
  events = [],
}: {
  monthLabel: string;
  days: number;
  events?: DSCalendarEvent[];
}) {
  const cells = Array.from({ length: days }, (_, index) => index + 1);

  return (
    <div className="ds-calendar" aria-label={monthLabel}>
      <div className="ds-calendar__header">
        <strong>{monthLabel}</strong>
        <span>{events.length} events</span>
      </div>
      <div className="ds-calendar__grid">
        {cells.map((day) => {
          const dayEvents = events.filter((event) => event.day === day);
          return (
            <div className="ds-calendar__day" key={day}>
              <strong>{day}</strong>
              {dayEvents.slice(0, 2).map((event) => (
                <span className={cx('ds-calendar__event', event.tone && `ds-calendar__event--${event.tone}`)} key={event.id}>
                  {event.title}
                </span>
              ))}
            </div>
          );
        })}
      </div>
    </div>
  );
}

export type DSKanbanColumn = {
  id: string;
  title: string;
  items: Array<{
    id: string;
    title: string;
    meta?: string;
    tone?: Tone;
  }>;
};

export function DSKanbanBoard({ columns }: { columns: DSKanbanColumn[] }) {
  return (
    <div className="ds-kanban" role="list">
      {columns.map((column) => (
        <section className="ds-kanban__column" key={column.id} role="listitem">
          <div className="ds-kanban__header">
            <strong>{column.title}</strong>
            <span>{column.items.length}</span>
          </div>
          <div className="ds-kanban__items">
            {column.items.map((item) => (
              <article className={cx('ds-kanban__card', item.tone && `ds-kanban__card--${item.tone}`)} key={item.id}>
                <strong>{item.title}</strong>
                {item.meta ? <small>{item.meta}</small> : null}
              </article>
            ))}
          </div>
        </section>
      ))}
    </div>
  );
}

export function DSFileUpload({
  label,
  hint,
  accept,
  multiple,
  onChange,
}: {
  label: string;
  hint?: string;
  accept?: InputHTMLAttributes<HTMLInputElement>['accept'];
  multiple?: boolean;
  onChange?: ChangeEventHandler<HTMLInputElement>;
}) {
  return (
    <label className="ds-file-upload">
      <input accept={accept} multiple={multiple} onChange={onChange} type="file" />
      <span className="ds-file-upload__icon" aria-hidden="true">
        +
      </span>
      <span>
        <strong>{label}</strong>
        {hint ? <small>{hint}</small> : null}
      </span>
    </label>
  );
}

export function DSRichTextEditor({
  label,
  actions,
  className,
  ...props
}: TextareaHTMLAttributes<HTMLTextAreaElement> & {
  label: string;
  actions?: ReactNode;
}) {
  return (
    <div className={cx('ds-rich-text', className)}>
      <div className="ds-rich-text__toolbar">
        <strong>{label}</strong>
        <div className="inline">
          {actions ?? (
            <>
              <DSButton size="sm" variant="ghost" type="button">
                B
              </DSButton>
              <DSButton size="sm" variant="ghost" type="button">
                I
              </DSButton>
              <DSButton size="sm" variant="ghost" type="button">
                Link
              </DSButton>
            </>
          )}
        </div>
      </div>
      <textarea className="ds-rich-text__input" {...props} />
    </div>
  );
}

export function DSVideoPlayer({
  title,
  meta,
  className,
  ...props
}: VideoHTMLAttributes<HTMLVideoElement> & {
  title?: string;
  meta?: string;
}) {
  return (
    <figure className={cx('ds-video-player', className)}>
      <video controls playsInline {...props} />
      {title || meta ? (
        <figcaption>
          {title ? <strong>{title}</strong> : null}
          {meta ? <small>{meta}</small> : null}
        </figcaption>
      ) : null}
    </figure>
  );
}

export function DSStatsGrid({
  stats,
  columns = 4,
}: {
  stats: Array<{
    label: string;
    value: ReactNode;
    hint?: string;
    tone?: Tone;
  }>;
  columns?: 2 | 3 | 4;
}) {
  return (
    <div className={cx('ds-stats-grid', `ds-stats-grid--${columns}`)}>
      {stats.map((stat) => (
        <DSStatCard key={stat.label} label={stat.label} value={stat.value} hint={stat.hint} tone={stat.tone} />
      ))}
    </div>
  );
}

export function DSComponentPreview({
  title,
  description,
  children,
  className,
}: HTMLAttributes<HTMLElement> & {
  title: string;
  description?: string;
  children: ReactNode;
}) {
  return (
    <DSCard className={cx('ds-component-preview', className)}>
      <div>
        <h3>{title}</h3>
        {description ? <p className="muted">{description}</p> : null}
      </div>
      {children}
    </DSCard>
  );
}

export { DSDataTable, DSStatCard };
