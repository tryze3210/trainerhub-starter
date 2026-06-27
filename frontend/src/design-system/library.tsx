import type {
  ChangeEventHandler,
  DragEvent,
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

export type DSPremiumChartPoint = {
  label: string;
  value: number;
  tone?: Tone;
};

export type DSDonutChartSegment = {
  label: string;
  value: number;
  tone?: Tone;
};

const toneColorVar: Record<Tone, string> = {
  primary: 'var(--color-primary)',
  success: 'var(--color-success)',
  warning: 'var(--color-warning)',
  danger: 'var(--color-danger)',
  neutral: 'var(--color-border-strong)',
};

function formatChartValue(value: number): string {
  return new Intl.NumberFormat('en-US', { maximumFractionDigits: 1 }).format(value);
}

function buildDonutGradient(segments: DSDonutChartSegment[]): string {
  const total = Math.max(
    segments.reduce((sum, segment) => sum + Math.max(segment.value, 0), 0),
    1,
  );
  let cursor = 0;
  const slices = segments.map((segment) => {
    const start = cursor;
    const end = cursor + (Math.max(segment.value, 0) / total) * 100;
    cursor = end;
    return `${toneColorVar[segment.tone ?? 'primary']} ${start}% ${end}%`;
  });

  return `conic-gradient(${slices.join(', ')})`;
}

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

export function DSPremiumLineChart({
  data,
  label,
  valueLabel,
}: {
  data: DSPremiumChartPoint[];
  label?: string;
  valueLabel?: string;
}) {
  const width = 320;
  const height = 160;
  const padding = 18;
  const values = data.map((item) => item.value);
  const min = Math.min(...values, 0);
  const max = Math.max(...values, 1);
  const span = Math.max(max - min, 1);
  const innerWidth = width - padding * 2;
  const innerHeight = height - padding * 2;
  const points = data.map((item, index) => {
    const x = padding + (data.length === 1 ? innerWidth / 2 : (index / (data.length - 1)) * innerWidth);
    const y = padding + innerHeight - ((item.value - min) / span) * innerHeight;
    return { ...item, x, y };
  });
  const polyline = points.map((point) => `${point.x},${point.y}`).join(' ');
  const area = `${padding},${height - padding} ${polyline} ${width - padding},${height - padding}`;

  return (
    <figure className="ds-premium-chart ds-line-chart" role="img" aria-label={label ?? 'Line chart'}>
      <div className="ds-premium-chart__header">
        <strong>{label ?? 'Trend'}</strong>
        {valueLabel ? <span>{valueLabel}</span> : null}
      </div>
      <svg className="ds-line-chart__svg" viewBox={`0 0 ${width} ${height}`} aria-hidden="true">
        <line className="ds-line-chart__grid" x1={padding} x2={width - padding} y1={padding} y2={padding} />
        <line className="ds-line-chart__grid" x1={padding} x2={width - padding} y1={height / 2} y2={height / 2} />
        <line className="ds-line-chart__grid" x1={padding} x2={width - padding} y1={height - padding} y2={height - padding} />
        <polygon className="ds-line-chart__area" points={area} />
        <polyline className="ds-line-chart__line" points={polyline} />
        {points.map((point) => (
          <circle className="ds-line-chart__point" cx={point.x} cy={point.y} key={point.label} r="4" />
        ))}
      </svg>
      <div className="ds-line-chart__axis">
        {points.map((point) => (
          <span key={point.label}>
            <small>{point.label}</small>
            <strong>{formatChartValue(point.value)}</strong>
          </span>
        ))}
      </div>
    </figure>
  );
}

export function DSDonutChart({
  segments,
  label,
  centerLabel,
}: {
  segments: DSDonutChartSegment[];
  label?: string;
  centerLabel?: string;
}) {
  const total = segments.reduce((sum, segment) => sum + Math.max(segment.value, 0), 0);

  return (
    <figure className="ds-premium-chart ds-donut-chart" role="img" aria-label={label ?? 'Donut chart'}>
      <div className="ds-premium-chart__header">
        <strong>{label ?? 'Breakdown'}</strong>
        <span>{formatChartValue(total)} total</span>
      </div>
      <div className="ds-donut-chart__body">
        <div className="ds-donut-chart__visual" style={{ background: buildDonutGradient(segments) }}>
          <div className="ds-donut-chart__hole">
            <strong>{centerLabel ?? formatChartValue(total)}</strong>
            <small>Total</small>
          </div>
        </div>
        <div className="ds-donut-chart__legend">
          {segments.map((segment) => (
            <span key={segment.label}>
              <i className={cx('ds-donut-chart__swatch', `ds-donut-chart__swatch--${segment.tone ?? 'primary'}`)} />
              <small>{segment.label}</small>
              <strong>{formatChartValue(segment.value)}</strong>
            </span>
          ))}
        </div>
      </div>
    </figure>
  );
}

export function DSInsightChartCard({
  title,
  metric,
  description,
  children,
}: {
  title: string;
  metric: ReactNode;
  description?: string;
  children: ReactNode;
}) {
  return (
    <DSCard className="ds-insight-chart-card">
      <div className="ds-insight-chart-card__header">
        <span>
          <strong>{title}</strong>
          {description ? <small>{description}</small> : null}
        </span>
        <strong>{metric}</strong>
      </div>
      {children}
    </DSCard>
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

export type DSKanbanMoveEvent = {
  cardId: string;
  fromColumnId: string;
  toColumnId: string;
};

const KANBAN_DRAG_TYPE = 'application/x-trainerhub-kanban-card';

function readKanbanDragPayload(event: DragEvent<HTMLElement>): DSKanbanMoveEvent | null {
  const raw = event.dataTransfer.getData(KANBAN_DRAG_TYPE) || event.dataTransfer.getData('text/plain');
  if (!raw) {
    return null;
  }

  try {
    const parsed = JSON.parse(raw) as Partial<DSKanbanMoveEvent>;
    if (!parsed.cardId || !parsed.fromColumnId) {
      return null;
    }
    return {
      cardId: parsed.cardId,
      fromColumnId: parsed.fromColumnId,
      toColumnId: parsed.toColumnId ?? '',
    };
  } catch {
    return null;
  }
}

export function DSKanbanBoard({
  columns,
  onCardMove,
}: {
  columns: DSKanbanColumn[];
  onCardMove?: (event: DSKanbanMoveEvent) => void;
}) {
  const isInteractive = Boolean(onCardMove);

  function handleDragStart(event: DragEvent<HTMLElement>, cardId: string, fromColumnId: string) {
    const payload: DSKanbanMoveEvent = { cardId, fromColumnId, toColumnId: fromColumnId };
    event.dataTransfer.effectAllowed = 'move';
    event.dataTransfer.setData(KANBAN_DRAG_TYPE, JSON.stringify(payload));
    event.dataTransfer.setData('text/plain', JSON.stringify(payload));
  }

  function handleDrop(event: DragEvent<HTMLElement>, toColumnId: string) {
    if (!onCardMove) {
      return;
    }

    event.preventDefault();
    const payload = readKanbanDragPayload(event);
    if (!payload) {
      return;
    }

    onCardMove({ ...payload, toColumnId });
  }

  return (
    <div className={cx('ds-kanban', isInteractive && 'ds-kanban--draggable')} role="list">
      {columns.map((column) => (
        <section
          className={cx('ds-kanban__column', isInteractive && 'ds-kanban__column--dropzone')}
          key={column.id}
          onDragOver={isInteractive ? (event) => event.preventDefault() : undefined}
          onDrop={isInteractive ? (event) => handleDrop(event, column.id) : undefined}
          role="listitem"
        >
          <div className="ds-kanban__header">
            <strong>{column.title}</strong>
            <span>{column.items.length}</span>
          </div>
          <div className="ds-kanban__items">
            {column.items.map((item) => (
              <article
                className={cx(
                  'ds-kanban__card',
                  isInteractive && 'ds-kanban__card--draggable',
                  item.tone && `ds-kanban__card--${item.tone}`,
                )}
                draggable={isInteractive}
                key={item.id}
                onDragStart={isInteractive ? (event) => handleDragStart(event, item.id, column.id) : undefined}
              >
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
