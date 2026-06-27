import type {
  ButtonHTMLAttributes,
  HTMLAttributes,
  InputHTMLAttributes,
  ReactNode,
  SelectHTMLAttributes,
  TextareaHTMLAttributes,
} from 'react';

type Tone = 'neutral' | 'primary' | 'success' | 'warning' | 'danger';
type Size = 'sm' | 'md' | 'lg';

function cx(...classes: Array<string | false | null | undefined>): string {
  return classes.filter(Boolean).join(' ');
}

export type DSCommandPaletteItem = {
  id: string;
  title: string;
  description?: string;
  group?: string;
  shortcut?: string;
  tone?: Tone;
  disabled?: boolean;
};

export function DSButton({
  variant = 'primary',
  size = 'md',
  className,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger';
  size?: Size;
}) {
  return <button className={cx('btn', variant !== 'primary' && variant, size !== 'md' && size, className)} {...props} />;
}

export function DSCard({
  tone = 'neutral',
  compact = false,
  className,
  ...props
}: HTMLAttributes<HTMLElement> & {
  tone?: Tone;
  compact?: boolean;
}) {
  return <article className={cx('card', compact && 'compact', tone !== 'neutral' && tone, className)} {...props} />;
}

export function DSBadge({
  tone = 'primary',
  className,
  ...props
}: HTMLAttributes<HTMLSpanElement> & {
  tone?: 'primary' | 'secondary' | 'success' | 'warning' | 'danger';
}) {
  return <span className={cx('badge', tone !== 'primary' && tone, className)} {...props} />;
}

export function DSTextField({
  label,
  hint,
  className,
  ...props
}: InputHTMLAttributes<HTMLInputElement> & {
  label: string;
  hint?: string;
}) {
  return (
    <label className={cx('form-group', className)}>
      <span className="label">{label}</span>
      <input className="input" {...props} />
      {hint ? <small>{hint}</small> : null}
    </label>
  );
}

export function DSTextArea({
  label,
  hint,
  className,
  ...props
}: TextareaHTMLAttributes<HTMLTextAreaElement> & {
  label: string;
  hint?: string;
}) {
  return (
    <label className={cx('form-group', className)}>
      <span className="label">{label}</span>
      <textarea className="textarea" {...props} />
      {hint ? <small>{hint}</small> : null}
    </label>
  );
}

export function DSSelect({
  label,
  hint,
  className,
  children,
  ...props
}: SelectHTMLAttributes<HTMLSelectElement> & {
  label: string;
  hint?: string;
}) {
  return (
    <label className={cx('form-group', className)}>
      <span className="label">{label}</span>
      <select className="select" {...props}>
        {children}
      </select>
      {hint ? <small>{hint}</small> : null}
    </label>
  );
}

export function DSModalShell({
  title,
  description,
  children,
  footer,
}: {
  title: string;
  description?: string;
  children: ReactNode;
  footer?: ReactNode;
}) {
  return (
    <div className="ds-modal" role="dialog" aria-modal="true" aria-labelledby="ds-modal-title">
      <div className="ds-modal__panel">
        <div className="stack" style={{ gap: 6 }}>
          <h2 id="ds-modal-title">{title}</h2>
          {description ? <p>{description}</p> : null}
        </div>
        <div>{children}</div>
        {footer ? <div className="ds-modal__footer">{footer}</div> : null}
      </div>
    </div>
  );
}

export function DSCommandPalette({
  title = 'Command palette',
  placeholder = 'Search actions, records, pages',
  query,
  items,
  emptyLabel = 'No results',
  onQueryChange,
  onSelect,
  onClose,
}: {
  title?: string;
  placeholder?: string;
  query: string;
  items: DSCommandPaletteItem[];
  emptyLabel?: string;
  onQueryChange: (value: string) => void;
  onSelect: (item: DSCommandPaletteItem) => void;
  onClose?: () => void;
}) {
  const groupedItems = items.reduce<Record<string, DSCommandPaletteItem[]>>((groups, item) => {
    const group = item.group ?? 'Actions';
    groups[group] = [...(groups[group] ?? []), item];
    return groups;
  }, {});

  return (
    <div className="ds-command-palette" role="dialog" aria-modal="true" aria-labelledby="ds-command-palette-title">
      <div className="ds-command-palette__panel">
        <div className="ds-command-palette__header">
          <div>
            <h2 id="ds-command-palette-title">{title}</h2>
            <small>Ctrl+K</small>
          </div>
          {onClose ? (
            <DSButton size="sm" variant="ghost" type="button" onClick={onClose} aria-label="Close command palette">
              Esc
            </DSButton>
          ) : null}
        </div>
        <input
          autoFocus
          className="ds-command-palette__search"
          onChange={(event) => onQueryChange(event.target.value)}
          placeholder={placeholder}
          type="search"
          value={query}
        />
        <div className="ds-command-palette__results" role="listbox">
          {items.length === 0 ? (
            <div className="ds-command-palette__empty">{emptyLabel}</div>
          ) : (
            Object.entries(groupedItems).map(([group, groupItems]) => (
              <section className="ds-command-palette__group" key={group}>
                <strong>{group}</strong>
                {groupItems.map((item) => (
                  <button
                    className={cx(
                      'ds-command-palette__item',
                      item.tone && item.tone !== 'neutral' && `ds-command-palette__item--${item.tone}`,
                    )}
                    disabled={item.disabled}
                    key={item.id}
                    onClick={() => onSelect(item)}
                    role="option"
                    type="button"
                  >
                    <span>
                      <strong>{item.title}</strong>
                      {item.description ? <small>{item.description}</small> : null}
                    </span>
                    {item.shortcut ? <kbd>{item.shortcut}</kbd> : null}
                  </button>
                ))}
              </section>
            ))
          )}
        </div>
      </div>
    </div>
  );
}

export function DSDataTable({
  columns,
  rows,
  getRowKey,
}: {
  columns: Array<{ key: string; label: string }>;
  rows: Array<Record<string, ReactNode>>;
  getRowKey?: (row: Record<string, ReactNode>, index: number) => string;
}) {
  return (
    <div className="table-wrap">
      <table className="table">
        <thead>
          <tr>
            {columns.map((column) => (
              <th key={column.key}>{column.label}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr key={getRowKey ? getRowKey(row, index) : String(index)}>
              {columns.map((column) => (
                <td key={column.key}>{row[column.key]}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function DSStatCard({
  label,
  value,
  hint,
  tone = 'neutral',
}: {
  label: string;
  value: ReactNode;
  hint?: string;
  tone?: Tone;
}) {
  return (
    <DSCard tone={tone} compact>
      <div className="kpi">
        <span className="muted">{label}</span>
        <strong>{value}</strong>
        {hint ? <small>{hint}</small> : null}
      </div>
    </DSCard>
  );
}
