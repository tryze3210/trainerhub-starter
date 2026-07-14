'use client';

import Link from 'next/link';
import { useMemo, useState } from 'react';
import type { ReactNode } from 'react';
import { adminReconciliationSnapshotsApi } from '@/modules/admin-reconciliation-snapshots/api';
import type {
  ReconciliationSnapshot,
  SnapshotCompareIssue,
  SnapshotCompareResponse,
  SnapshotMetricsResponse,
  SnapshotRetentionResponse,
  SnapshotScheduleResponse,
  SnapshotSectionStatus,
  SnapshotSource,
  SnapshotStatus,
  SnapshotTrendPoint,
  SnapshotTrendResponse,
} from '@/modules/admin-reconciliation-snapshots/api';

export function label(value: string) {
  const labels: Record<string, string> = {
    access: 'Доступы',
    async: 'Фоновые задачи',
    billing: 'Оплаты',
    entitlement: 'Доступы',
    ledger: 'Реестр',
    money: 'Деньги',
    orders: 'Заказы',
    payout: 'Выплаты',
    payment: 'Платежи',
    subscriptions: 'Подписки',
    webhook: 'Вебхуки',
  };
  return labels[value] || value.replaceAll('_', ' ');
}

export function formatDate(value?: string | null) {
  if (!value) return '—';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString('ru-RU');
}

export function formatNumber(value: unknown) {
  const parsed = Number(value || 0);
  return Number.isFinite(parsed) ? parsed.toLocaleString('ru-RU') : '0';
}

export function numberValue(value: unknown) {
  const parsed = Number(value || 0);
  return Number.isFinite(parsed) ? parsed : 0;
}

export function scalar(value: unknown, fallback = '—') {
  if (value === null || value === undefined || value === '') return fallback;
  if (typeof value === 'number') return value.toLocaleString('ru-RU');
  if (typeof value === 'boolean') return value ? 'да' : 'нет';
  if (Array.isArray(value)) return `${value.length} шт.`;
  if (typeof value === 'object') return JSON.stringify(value);
  return String(value);
}

export function statusTitle(status?: SnapshotStatus) {
  if (!status) return 'Неизвестно';
  if (status === 'ok') return 'В норме';
  if (status === 'degraded') return 'Есть замечания';
  if (status === 'warning') return 'Предупреждение';
  if (status === 'critical') return 'Критично';
  if (status === 'missing') return 'Нет данных';
  if (status === 'failed') return 'Ошибка';
  return status;
}

export function sourceTitle(source?: SnapshotSource) {
  if (!source) return 'Любой источник';
  if (source === 'manual') return 'Ручной';
  if (source === 'scheduled') return 'Плановый';
  if (source === 'repair') return 'Исправление';
  if (source === 'ci') return 'Автопроверка';
  return source;
}

function deltaLabel(value?: number) {
  const numeric = Number(value || 0);
  if (numeric > 0) return `+${numeric}`;
  return String(numeric);
}

function directionHint(direction?: string) {
  if (direction === 'improved') return 'Проблем стало меньше';
  if (direction === 'worsened') return 'Проблем стало больше';
  if (direction === 'unchanged') return 'Количество проблем не изменилось';
  if (direction === 'baseline') return 'Это базовый снимок без сравнения';
  return 'Сравнение рассчитано сервером';
}

function directionTitle(direction?: string) {
  if (direction === 'improved') return 'Улучшилось';
  if (direction === 'worsened') return 'Ухудшилось';
  if (direction === 'unchanged') return 'Без изменений';
  if (direction === 'baseline') return 'Базовый снимок';
  return direction || '—';
}

function badgeClass(status?: string) {
  if (status === 'ok' || status === 'improved') return 'badge success';
  if (status === 'critical' || status === 'failed' || status === 'worsened') return 'badge danger';
  if (status === 'degraded' || status === 'warning') return 'badge warning';
  return 'badge secondary';
}

function snapshotHref(snapshot?: ReconciliationSnapshot | null) {
  if (!snapshot?.id) return '#';
  return snapshot.href || `/admin/entities/reconciliation_snapshot/${snapshot.id}`;
}

function lastSegment(id?: string | null) {
  if (!id) return '—';
  return id.length > 12 ? id.slice(0, 8) : id;
}

function PanelHeader({ eyebrow, title, description, action }: { eyebrow?: string; title: string; description?: string; action?: ReactNode }) {
  return (
    <div className="admin-snapshot-panel-header">
      <div className="admin-snapshot-panel-copy">
        {eyebrow ? <span className="badge secondary">{eyebrow}</span> : null}
        <h2 style={{ marginTop: eyebrow ? 10 : 0 }}>{title}</h2>
        {description ? <p>{description}</p> : null}
      </div>
      {action ? <div className="admin-snapshot-panel-actions">{action}</div> : null}
    </div>
  );
}

function StatCard({ title, value, hint, badge }: { title: string; value: ReactNode; hint?: string; badge?: ReactNode }) {
  return (
    <div className="card compact admin-snapshot-stat">
      <div className="admin-snapshot-stat-row">
        <div className="kpi">
          <small>{title}</small>
          <strong>{value}</strong>
          {hint ? <small>{hint}</small> : null}
        </div>
        {badge}
      </div>
    </div>
  );
}

function EmptyState({ children }: { children: ReactNode }) {
  return <div className="empty-state">{children}</div>;
}

function SectionMiniGrid({ sectionStatuses }: { sectionStatuses?: Record<string, SnapshotSectionStatus> }) {
  const rows = Object.entries(sectionStatuses || {});
  if (!rows.length) {
    return <EmptyState>Статусы разделов отсутствуют в последнем снимке.</EmptyState>;
  }

  return (
    <div className="grid-3">
      {rows.map(([sectionKey, section]) => (
        <div className="card compact shadow-none" key={sectionKey}>
          <div className="admin-snapshot-card-row">
            <strong>{label(sectionKey)}</strong>
            <span className={badgeClass(section.status)}>{statusTitle(section.status)}</span>
          </div>
          <small>
            {formatNumber(section.issue_count ?? section.total_issues)} проблем · {formatNumber(section.critical_count)} критично ·{' '}
            {formatNumber(section.warning_count)} предупреждений
          </small>
        </div>
      ))}
    </div>
  );
}

export function ReconciliationHealthCard({
  latestSnapshot,
  metrics,
  schedule,
}: {
  latestSnapshot?: ReconciliationSnapshot | null;
  metrics?: SnapshotMetricsResponse | null;
  schedule?: SnapshotScheduleResponse | null;
}) {
  const headline = metrics?.headline;
  const current = latestSnapshot || null;
  const status = current?.status || headline?.latest_status || metrics?.status || 'missing';
  const totalIssues = current?.total_issues ?? headline?.latest_total_issues ?? 0;
  const criticalCount = current?.critical_count ?? headline?.latest_critical_count ?? 0;
  const totalDelta = headline?.total_issues_delta;
  const criticalDelta = headline?.critical_count_delta;

  return (
    <div className="card hero">
      <PanelHeader
        eyebrow="Сводка состояния"
        title="Состояние сверки"
        description="Короткая сводка последнего сохраненного снимка и состояния запланированного захвата."
        action={current?.id ? <Link className="btn secondary sm" href={snapshotHref(current)}>Открыть снимок</Link> : null}
      />

      <div className="grid-4">
        <StatCard title="Статус" value={statusTitle(status)} hint={formatDate(current?.generated_at || headline?.latest_generated_at)} badge={<span className={badgeClass(status)}>{statusTitle(status)}</span>} />
        <StatCard title="Всего проблем" value={formatNumber(totalIssues)} hint={totalDelta !== undefined ? `${deltaLabel(totalDelta)} к предыдущему` : 'последний снимок'} />
        <StatCard title="Критично" value={formatNumber(criticalCount)} hint={criticalDelta !== undefined ? `${deltaLabel(criticalDelta)} критичных` : 'критичные проблемы'} />
        <StatCard title="Плановый снимок" value={schedule?.due ? 'Пора создать' : 'Не требуется'} hint={schedule?.next_capture_due_at ? `следующий: ${formatDate(schedule.next_capture_due_at)}` : schedule?.message || 'контролируется сервером'} badge={<span className={badgeClass(schedule?.due ? 'degraded' : 'ok')}>{schedule?.due ? 'требуется' : 'в норме'}</span>} />
      </div>

      <div style={{ marginTop: 20 }}>
        <SectionMiniGrid sectionStatuses={current?.section_statuses} />
      </div>
    </div>
  );
}

export function ReconciliationSnapshotTrend({ trend, metrics }: { trend?: SnapshotTrendResponse | null; metrics?: SnapshotMetricsResponse | null }) {
  const points = useMemo(() => {
    const trendPoints = trend?.points || [];
    const metricPoints = metrics?.trend?.points || [];
    return trendPoints.length ? trendPoints : metricPoints;
  }, [metrics, trend]);

  const visiblePoints = points.slice(-24);
  const maxIssues = Math.max(...visiblePoints.map((point) => numberValue(point.total_issues)), 1);

  return (
    <div className="card">
      <PanelHeader
        eyebrow="Динамика"
        title="Динамика снимков"
        description="Как менялось количество проблем по последним ручным, плановым и исправляющим снимкам."
        action={trend?.delta ? <span className={badgeClass(trend.delta.direction)}>{directionTitle(trend.delta.direction)}</span> : null}
      />

      {!visiblePoints.length ? (
        <EmptyState>Истории снимков пока нет. Создай ручной снимок или дождись запланированного захвата.</EmptyState>
      ) : (
        <div className="stack">
          {visiblePoints.map((point: SnapshotTrendPoint) => {
            const width = Math.max(4, Math.round((numberValue(point.total_issues) / maxIssues) * 100));
            return (
              <div className="card compact shadow-none" key={point.id}>
                <div className="admin-snapshot-card-row">
                  <div>
                    <strong>{formatDate(point.generated_at)}</strong>
                    <p>
                      {sourceTitle(point.source)} · {statusTitle(point.status)} · критично: {formatNumber(point.critical_count)}
                    </p>
                  </div>
                  <strong>{formatNumber(point.total_issues)} проблем</strong>
                </div>
                <div style={{ height: 10, borderRadius: 999, background: 'var(--bg-muted)', overflow: 'hidden' }}>
                  <div style={{ width: `${width}%`, height: '100%', borderRadius: 999, background: 'var(--primary)' }} />
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

export function ReconciliationRepairImpact({ metrics, repairSnapshots }: { metrics?: SnapshotMetricsResponse | null; repairSnapshots: ReconciliationSnapshot[] }) {
  const repair = metrics?.repair_effectiveness;

  return (
    <div className="card">
      <PanelHeader
        eyebrow="Исправления"
        title="Эффективность исправлений"
        description="Показывает, помогают ли исправляющие действия реально уменьшать число проблем сверки."
      />

      <div className="grid-4">
        <StatCard title="Снимки исправлений" value={formatNumber(repair?.total ?? repairSnapshots.length)} hint="созданы после исправлений" />
        <StatCard title="Улучшилось" value={formatNumber(repair?.improved)} hint="проблем стало меньше" badge={<span className="badge success">лучше</span>} />
        <StatCard title="Ухудшилось" value={formatNumber(repair?.worsened)} hint="проблем стало больше" badge={<span className="badge danger">риск</span>} />
        <StatCard title="Без изменений" value={formatNumber(repair?.unchanged)} hint="видимой дельты нет" />
      </div>

      <div className="divider" />

      {!repairSnapshots.length ? (
        <EmptyState>Снимков исправлений пока нет. Они появятся после исправления из отчета сверки.</EmptyState>
      ) : (
        <div className="stack">
          {repairSnapshots.slice(0, 5).map((snapshot) => {
            const delta = snapshot.delta;
            return (
              <div className="card compact shadow-none" key={snapshot.id}>
                <div className="admin-snapshot-card-row">
                  <div>
                    <strong>Снимок исправления {lastSegment(snapshot.id)}</strong>
                    <p>{formatDate(snapshot.generated_at)} · связка {snapshot.correlation_id || '—'}</p>
                  </div>
                  <span className={badgeClass(delta?.direction)}>{delta ? directionTitle(delta.direction) : statusTitle(snapshot.status)}</span>
                </div>
                <small>
                  всего {formatNumber(snapshot.total_issues)} · критично {formatNumber(snapshot.critical_count)}
                  {delta ? ` · изменение ${deltaLabel(delta.total_issues_delta)}` : ''}
                </small>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

function issueTitle(issue: SnapshotCompareIssue) {
  return issue.message || issue.code || issue.key || `${label(String(issue.entity_type || 'сущность'))}:${issue.entity_id || 'неизвестно'}`;
}

function IssueList({ title, rows, empty }: { title: string; rows?: SnapshotCompareIssue[]; empty: string }) {
  const list = rows || [];
  return (
    <div className="card compact shadow-none">
      <div className="admin-snapshot-card-row">
        <h3>{title}</h3>
        <span className="badge secondary">{list.length}</span>
      </div>
      {!list.length ? (
        <small>{empty}</small>
      ) : (
        <ul className="list">
          {list.slice(0, 8).map((issue, index) => (
            <li className="list-item" key={`${issue.key || issue.code || title}-${index}`}>
              <strong>{issueTitle(issue)}</strong>
              <small>
                {issue.section ? `${issue.section} · ` : ''}
                {statusTitle(String(issue.severity || issue.current_severity || issue.previous_severity || 'unknown'))} · {label(String(issue.entity_type || 'сущность'))}:{issue.entity_id || '—'}
              </small>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export function ReconciliationComparePanel({ snapshots }: { snapshots: ReconciliationSnapshot[] }) {
  const defaultCurrentSnapshot = snapshots[0]?.id || '';
  const defaultBaselineSnapshot = snapshots[1]?.id || '';
  const [baselineId, setBaselineId] = useState(defaultBaselineSnapshot);
  const [currentId, setCurrentId] = useState(defaultCurrentSnapshot);
  const [compare, setCompare] = useState<SnapshotCompareResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [msg, setMsg] = useState('');

  const runCompare = async () => {
    try {
      setIsLoading(true);
      setMsg('');
      setCompare(
        await adminReconciliationSnapshotsApi.compare({
          baseline_id: baselineId || undefined,
          current_id: currentId || undefined,
        })
      );
    } catch (error) {
      setMsg(error instanceof Error ? error.message : 'Не удалось сравнить снимки');
    } finally {
      setIsLoading(false);
    }
  };

  const summary = compare?.summary;
  const direction = summary?.direction;

  return (
    <div className="card">
      <PanelHeader
        eyebrow="Сравнить"
        title="Сравнение снимков"
        description="Выберите два снимка: система покажет, какие проблемы исчезли, появились или остались."
        action={<button className="btn sm" type="button" disabled={isLoading || snapshots.length < 2} onClick={() => void runCompare()}>{isLoading ? 'Сравниваем...' : 'Сравнить'}</button>}
      />

      <div className="form-row">
        <label className="form-group">
          <span className="label">Базовый снимок</span>
          <select className="select" value={baselineId} onChange={(event) => setBaselineId(event.target.value)}>
            <option value="">Авто: базовый</option>
            {snapshots.map((snapshot) => (
              <option key={snapshot.id} value={snapshot.id}>
                {formatDate(snapshot.generated_at)} · {sourceTitle(snapshot.source)} · {lastSegment(snapshot.id)}
              </option>
            ))}
          </select>
        </label>
        <label className="form-group">
          <span className="label">Текущий снимок</span>
          <select className="select" value={currentId} onChange={(event) => setCurrentId(event.target.value)}>
            <option value="">Авто: текущий</option>
            {snapshots.map((snapshot) => (
              <option key={snapshot.id} value={snapshot.id}>
                {formatDate(snapshot.generated_at)} · {sourceTitle(snapshot.source)} · {lastSegment(snapshot.id)}
              </option>
            ))}
          </select>
        </label>
      </div>

      {msg ? <div className="card error compact">{msg}</div> : null}

      {compare ? (
        <>
          <div className="grid-4" style={{ marginTop: 16 }}>
            <StatCard title="Итог" value={directionTitle(direction)} hint={directionHint(direction)} badge={direction ? <span className={badgeClass(direction)}>{directionTitle(direction)}</span> : null} />
            <StatCard title="Дельта проблем" value={deltaLabel(summary?.total_issues_delta)} hint="текущий - базовый" />
            <StatCard title="Закрыто" value={formatNumber(summary?.resolved_count ?? compare.resolved?.length)} hint="исчезнувшие проблемы" />
            <StatCard title="Добавлено" value={formatNumber(summary?.added_count ?? compare.added?.length)} hint="новые проблемы" />
          </div>
          <div className="grid-3" style={{ marginTop: 16 }}>
            <IssueList title="Закрыто" rows={compare.resolved} empty="Закрытых проблем нет." />
            <IssueList title="Добавлено" rows={compare.added} empty="Новых проблем нет." />
            <IssueList title="Осталось" rows={compare.persisted} empty="Повторяющихся проблем нет." />
          </div>
        </>
      ) : (
        <EmptyState>Выберите два снимка и нажмите «Сравнить». Если оставить поля пустыми, сервер сравнит последние два снимка автоматически.</EmptyState>
      )}
    </div>
  );
}

function retentionCount(value: SnapshotRetentionResponse | null, key: 'candidate_count' | 'deleted_count' | 'protected_count') {
  if (!value) return 0;
  const direct = numberValue(value[key]);
  if (direct) return direct;
  if (key === 'candidate_count') return (value.candidates || []).length;
  if (key === 'protected_count') return (value.protected_snapshots || value.protected || []).length;
  return 0;
}

export function ReconciliationRetentionPanel({ initialPreview, onChanged }: { initialPreview?: SnapshotRetentionResponse | null; onChanged: () => void }) {
  const [source, setSource] = useState('scheduled');
  const [keepMin, setKeepMin] = useState(5);
  const [confirmОчистить, setConfirmОчистить] = useState(false);
  const [preview, setPreview] = useState<SnapshotRetentionResponse | null>(initialPreview || null);
  const [isLoading, setIsLoading] = useState(false);
  const [msg, setMsg] = useState('');

  const payload = {
    dry_run: true,
    source: source || undefined,
    keep_min_per_source: keepMin,
  };

  const runPreview = async () => {
    try {
      setIsLoading(true);
      setMsg('');
      setPreview(await adminReconciliationSnapshotsApi.pruneRetention(payload));
    } catch (error) {
      setMsg(error instanceof Error ? error.message : 'Не удалось посчитать предпросмотр очистки');
    } finally {
      setIsLoading(false);
    }
  };

  const runОчистить = async () => {
    if (!confirmОчистить) {
      setMsg('Подтвердите очистку: старые снимки будут удалены по правилам хранения.');
      return;
    }

    try {
      setIsLoading(true);
      setMsg('');
      const result = await adminReconciliationSnapshotsApi.pruneRetention({ ...payload, dry_run: false });
      setPreview(result);
      setMsg(`Очистка завершена. Удалено: ${retentionCount(result, 'deleted_count')}.`);
      setConfirmОчистить(false);
      onChanged();
    } catch (error) {
      setMsg(error instanceof Error ? error.message : 'Не удалось выполнить очистку');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="card">
      <PanelHeader
        eyebrow="Хранение"
        title="Хранение снимков"
        description="Удаляет старые служебные снимки и оставляет последние записи для проверки истории."
        action={
          <div className="inline">
            <button className="btn secondary sm" type="button" disabled={isLoading} onClick={() => void runPreview()}>{isLoading ? 'Загрузка...' : 'Проверить'}</button>
            <button className="btn danger sm" type="button" disabled={isLoading} onClick={() => void runОчистить()}>Очистить</button>
          </div>
        }
      />

      <div className="form-row">
        <label className="form-group">
          <span className="label">Источник</span>
          <select className="select" value={source} onChange={(event) => setSource(event.target.value)}>
            <option value="">Все источники</option>
            <option value="scheduled">Плановый</option>
            <option value="repair">Исправление</option>
            <option value="manual">Ручной</option>
            <option value="ci">Автопроверка</option>
          </select>
        </label>
        <label className="form-group">
          <span className="label">Минимум на источник</span>
          <select className="select" value={keepMin} onChange={(event) => setKeepMin(Number(event.target.value))}>
            {[3, 5, 10, 20].map((value) => (
              <option key={value} value={value}>{value}</option>
            ))}
          </select>
        </label>
      </div>

      <label className="checkbox-inline" style={{ marginTop: 12 }}>
        <input type="checkbox" checked={confirmОчистить} onChange={(event) => setConfirmОчистить(event.target.checked)} />
        Подтверждаю удаление старых снимков по правилам хранения
      </label>

      {msg ? <div className="card warning compact" style={{ marginTop: 12 }}>{msg}</div> : null}

      <div className="grid-3" style={{ marginTop: 16 }}>
        <StatCard title="К удалению" value={formatNumber(retentionCount(preview, 'candidate_count'))} hint="будут удалены при очистке" />
        <StatCard title="Защищено" value={formatNumber(retentionCount(preview, 'protected_count'))} hint="последние записи сохранены" />
        <StatCard title="Удалено" value={formatNumber(retentionCount(preview, 'deleted_count'))} hint={preview?.dry_run === false ? 'результат последней очистки' : 'режим проверки'} />
      </div>
    </div>
  );
}

export function SnapshotHistoryPanel({ snapshots }: { snapshots: ReconciliationSnapshot[] }) {
  return (
    <div className="card">
      <PanelHeader eyebrow="История" title="Последние снимки" description="Последние сохраненные состояния сверки. Открывайте запись только если нужно посмотреть подробности." />
      {!snapshots.length ? (
        <EmptyState>История снимков пустая. Нажмите «Создать снимок», чтобы сохранить первое состояние.</EmptyState>
      ) : (
        <div className="table-wrap">
          <table className="table">
            <thead>
              <tr>
                <th>Создано</th>
                <th>Источник</th>
                <th>Статус</th>
                <th>Проблемы</th>
                <th>Критично</th>
                <th>Связка</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {snapshots.slice(0, 25).map((snapshot) => (
                <tr key={snapshot.id}>
                  <td>{formatDate(snapshot.generated_at)}</td>
                  <td>{sourceTitle(snapshot.source)}</td>
                  <td><span className={badgeClass(snapshot.status)}>{statusTitle(snapshot.status)}</span></td>
                  <td>{formatNumber(snapshot.total_issues)}</td>
                  <td>{formatNumber(snapshot.critical_count)}</td>
                  <td>{snapshot.correlation_id || '—'}</td>
                  <td><Link className="btn secondary sm" href={snapshotHref(snapshot)}>Открыть</Link></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
