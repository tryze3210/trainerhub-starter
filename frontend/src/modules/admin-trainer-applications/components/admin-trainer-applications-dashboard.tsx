'use client';

import { useEffect, useMemo, useState } from 'react';
import { ErrorCard, LoadingCard } from '@/components/async-state';
import {
  adminTrainerApplicationsApi,
  type AdminTrainerApplication,
  type TrainerApplicationReadinessIssue,
  type TrainerApplicationReadinessResponse,
} from '@/modules/admin-trainer-applications/api';

const statusFilters = ['', 'draft', 'submitted', 'under_review', 'approved', 'changes_requested', 'rejected'];

function badgeTone(status: string): 'secondary' | 'warning' | 'success' | 'danger' {
  if (status === 'approved' || status === 'healthy') return 'success';
  if (status === 'rejected' || status === 'critical' || status === 'degraded') return 'danger';
  if (status === 'submitted' || status === 'under_review' || status === 'changes_requested' || status === 'warning') return 'warning';
  return 'secondary';
}

function formatDateTime(value?: string | null) {
  if (!value) return '—';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date);
}

function stringify(value: unknown) {
  if (value === null || value === undefined || value === '') return '—';
  if (typeof value === 'object') return JSON.stringify(value);
  return String(value);
}

function issueActionLabel(issue: TrainerApplicationReadinessIssue) {
  if (issue.code.startsWith('approved_without_') || issue.code === 'approved_profile_not_dashboard_ready') {
    return 'Sync access';
  }
  if (issue.code === 'stale_trainer_application_review') return 'Review now';
  if (issue.code === 'review_queue_incomplete_application') return 'Request changes';
  return 'Open queue item';
}

function ReadinessMetric({ label, value, tone }: { label: string; value: string | number; tone?: string }) {
  return (
    <article className={`card stack ${tone || ''}`} style={{ gap: 6 }}>
      <span className="muted">{label}</span>
      <strong className="stat-value">{value}</strong>
    </article>
  );
}

function ReadinessPanel({
  readiness,
  onRefresh,
  onSyncAccess,
  busyId,
}: {
  readiness: TrainerApplicationReadinessResponse | null;
  onRefresh: () => void;
  onSyncAccess: (applicationId: string) => void;
  busyId: string | null;
}) {
  if (!readiness) {
    return (
      <section className="card stack" style={{ gap: 12 }}>
        <div className="row">
          <div>
            <span className="badge secondary">Readiness</span>
            <h2 className="title-md" style={{ marginTop: 8 }}>Application readiness</h2>
            <p className="muted">Backend readiness endpoint пока не вернул данные.</p>
          </div>
          <button className="button secondary" type="button" onClick={onRefresh}>Обновить</button>
        </div>
      </section>
    );
  }

  const summary = readiness.summary;
  const critical = summary.critical_count || 0;
  const warning = summary.warning_count || 0;
  const info = summary.info_count || 0;

  return (
    <section className="card stack" style={{ gap: 16 }}>
      <div className="row" style={{ alignItems: 'flex-start' }}>
        <div>
          <span className={`badge ${badgeTone(readiness.status)}`}>readiness: {readiness.status}</span>
          <h2 className="title-md" style={{ marginTop: 8 }}>Application readiness</h2>
          <p className="muted">
            Проверяет approved access gaps, stale reviews, incomplete applications и dashboard unlock. Generated: {formatDateTime(readiness.generated_at)}.
          </p>
        </div>
        <button className="button secondary" type="button" onClick={onRefresh}>Обновить readiness</button>
      </div>

      <div className="grid-4">
        <ReadinessMetric label="Applications" value={summary.total_applications} />
        <ReadinessMetric label="Review queue" value={summary.review_queue_count} />
        <ReadinessMetric label="Dashboard ready" value={`${summary.dashboard_ready_count}/${summary.approved_count}`} tone={summary.approved_count !== summary.dashboard_ready_count ? 'warning' : undefined} />
        <ReadinessMetric label="Issues" value={`${summary.issue_count} total`} tone={critical ? 'danger' : warning ? 'warning' : undefined} />
      </div>

      <div className="grid-3">
        <ReadinessMetric label="Critical" value={critical} tone={critical ? 'danger' : undefined} />
        <ReadinessMetric label="Warning" value={warning} tone={warning ? 'warning' : undefined} />
        <ReadinessMetric label="Info" value={info} />
      </div>

      {readiness.recommendations.length ? (
        <div className="warning-banner">
          {readiness.recommendations.map((item) => (
            <p key={item} style={{ margin: 0 }}>{item}</p>
          ))}
        </div>
      ) : null}

      <div className="grid-2">
        {readiness.checks.map((check) => (
          <article className="card stack" key={check.code} style={{ gap: 8 }}>
            <span className={`badge ${badgeTone(check.status)}`}>{check.status}</span>
            <strong>{check.code}</strong>
            <p className="muted" style={{ margin: 0 }}>{check.description}</p>
          </article>
        ))}
      </div>

      <div className="stack" style={{ gap: 10 }}>
        <div className="row">
          <h3 className="title-sm">Readiness issues</h3>
          <span className="muted">{readiness.issues.length} shown</span>
        </div>
        {readiness.issues.map((issue, index) => {
          const applicationId = issue.application_id || issue.application?.id || '';
          const canSync = Boolean(applicationId && (issue.code.startsWith('approved_without_') || issue.code === 'approved_profile_not_dashboard_ready'));
          return (
            <article className="card stack" key={`${issue.code}:${applicationId || index}`} style={{ gap: 10 }}>
              <div className="row" style={{ alignItems: 'flex-start' }}>
                <div>
                  <span className={`badge ${badgeTone(issue.severity)}`}>{issue.severity}</span>
                  <h4 className="title-sm" style={{ marginTop: 8 }}>{issue.code}</h4>
                  <p className="muted" style={{ margin: 0 }}>{issue.message}</p>
                </div>
                <div className="stack" style={{ gap: 4, alignItems: 'flex-end' }}>
                  <span className="muted">{issue.user_email || issue.application?.user.email || 'user n/a'}</span>
                  <span className="badge secondary">{issue.application_status || issue.application?.status || 'status n/a'}</span>
                </div>
              </div>
              {issue.remediation ? <div className="warning-banner">{issue.remediation}</div> : null}
              {issue.details ? <pre className="code-block">{stringify(issue.details)}</pre> : null}
              {applicationId ? (
                <div className="inline">
                  <button
                    className="button secondary"
                    type="button"
                    disabled={!canSync || busyId === applicationId}
                    onClick={() => onSyncAccess(applicationId)}
                  >
                    {issueActionLabel(issue)}
                  </button>
                  <span className="muted">application {applicationId}</span>
                </div>
              ) : null}
            </article>
          );
        })}
        {readiness.issues.length === 0 ? <div className="success-banner">Readiness gaps не найдены.</div> : null}
      </div>
    </section>
  );
}

export function AdminTrainerApplicationsDashboard() {
  const [applications, setApplications] = useState<AdminTrainerApplication[]>([]);
  const [readiness, setReadiness] = useState<TrainerApplicationReadinessResponse | null>(null);
  const [status, setStatus] = useState('under_review');
  const [search, setSearch] = useState('');
  const [reviewNote, setReviewNote] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [mutatingId, setMutatingId] = useState<string | null>(null);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');

  async function load() {
    try {
      setLoading(true);
      setError('');
      const [listPayload, readinessPayload] = await Promise.all([
        adminTrainerApplicationsApi.list({ status, search, limit: 100 }),
        adminTrainerApplicationsApi.getReadiness({ limit: 50, stale_after_days: 7 }),
      ]);
      setApplications(listPayload.results);
      setReadiness(readinessPayload);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось загрузить заявки тренеров');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, [status]);

  async function review(application: AdminTrainerApplication, decision: 'approve' | 'reject' | 'request_changes' | 'under_review') {
    const id = application.id || '';
    if (!id) return;
    try {
      setMutatingId(id);
      setMessage('');
      setError('');
      const response = await adminTrainerApplicationsApi.review(id, {
        decision,
        reviewer_note: reviewNote[id] || (decision === 'approve' ? 'Approved from admin trainer onboarding queue.' : ''),
      });
      setMessage(`Заявка ${response.application.user.email} обновлена: ${response.application.status}`);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось применить решение');
    } finally {
      setMutatingId(null);
    }
  }

  async function syncAccessById(applicationId: string) {
    if (!applicationId) return;
    try {
      setMutatingId(applicationId);
      setMessage('');
      setError('');
      const response = await adminTrainerApplicationsApi.syncAccess(applicationId);
      setMessage(`Access sync выполнен для ${response.application.user.email}`);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось синхронизировать доступ');
    } finally {
      setMutatingId(null);
    }
  }

  async function syncAccess(application: AdminTrainerApplication) {
    await syncAccessById(application.id || '');
  }

  const statusSummary = useMemo(() => {
    const counts = new Map<string, number>();
    applications.forEach((application) => counts.set(application.status, (counts.get(application.status) || 0) + 1));
    return Array.from(counts.entries()).sort(([left], [right]) => left.localeCompare(right));
  }, [applications]);

  if (loading && applications.length === 0 && !readiness) return <LoadingCard text="Загружаем trainer applications" />;
  if (error && applications.length === 0 && !readiness) return <ErrorCard text={`Trainer applications недоступны: ${error}`} />;

  return (
    <div className="stack" style={{ gap: 24 }}>
      <ReadinessPanel readiness={readiness} onRefresh={() => void load()} onSyncAccess={(id) => void syncAccessById(id)} busyId={mutatingId} />

      <section className="card stack" style={{ gap: 16 }}>
        <div className="row">
          <div>
            <span className="badge secondary">Admin moderation</span>
            <h2 className="title-md" style={{ marginTop: 10 }}>Trainer applications</h2>
            <p className="muted">Approve выдаёт trainer role, создаёт/sync profile и открывает trainer dashboard.</p>
          </div>
          <button className="button secondary" type="button" onClick={() => void load()} disabled={loading}>
            Обновить
          </button>
        </div>

        <div className="grid-3">
          <label className="form-group">
            <span className="label">Status</span>
            <select className="input" value={status} onChange={(event) => setStatus(event.target.value)}>
              {statusFilters.map((item) => (
                <option key={item || 'all'} value={item}>{item || 'all'}</option>
              ))}
            </select>
          </label>
          <label className="form-group">
            <span className="label">Search</span>
            <input className="input" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="email / brand / city" />
          </label>
          <div className="form-group" style={{ justifyContent: 'flex-end' }}>
            <button className="button" type="button" onClick={() => void load()}>
              Найти
            </button>
          </div>
        </div>

        {statusSummary.length ? (
          <div className="inline">
            {statusSummary.map(([item, count]) => (
              <span key={item} className={`badge ${badgeTone(item)}`}>{item}: {count}</span>
            ))}
          </div>
        ) : null}

        {message ? <div className="success-banner">{message}</div> : null}
        {error ? <div className="error-banner">{error}</div> : null}
      </section>

      <section className="stack" style={{ gap: 16 }}>
        {applications.map((application) => {
          const id = application.id || '';
          const isBusy = mutatingId === id;
          return (
            <article key={id} className="card stack" style={{ gap: 14 }}>
              <div className="row" style={{ alignItems: 'flex-start' }}>
                <div>
                  <span className={`badge ${badgeTone(application.status)}`}>{application.status}</span>
                  <h3 className="title-md" style={{ marginTop: 8 }}>{application.brand_name || application.legal_name || application.user.email}</h3>
                  <p className="muted">{application.user.email} · {application.city || 'city n/a'} · {application.experience_years || 0} years</p>
                </div>
                <div className="stack" style={{ gap: 6, alignItems: 'flex-end' }}>
                  <span className="badge secondary">role: {application.user.role}</span>
                  <span className="badge secondary">profile: {application.profile?.status || 'missing'}</span>
                  <span className={`badge ${application.reviewable ? 'success' : 'secondary'}`}>reviewable: {String(application.reviewable)}</span>
                </div>
              </div>

              <p>{application.bio || 'No bio yet.'}</p>
              <div className="inline">
                {(application.specialties || []).map((specialty) => (
                  <span key={specialty} className="badge secondary">{specialty}</span>
                ))}
              </div>

              {application.reviewer_note ? <div className="warning-banner">Last note: {application.reviewer_note}</div> : null}

              <label className="form-group">
                <span className="label">Reviewer note</span>
                <textarea
                  className="textarea"
                  rows={3}
                  value={reviewNote[id] || ''}
                  onChange={(event) => setReviewNote((prev) => ({ ...prev, [id]: event.target.value }))}
                  placeholder="Обязателен для reject/request changes"
                />
              </label>

              <div className="inline">
                <button className="button" type="button" disabled={isBusy || !id} onClick={() => void review(application, 'approve')}>Approve</button>
                <button className="button secondary" type="button" disabled={isBusy || !id} onClick={() => void review(application, 'under_review')}>Under review</button>
                <button className="button secondary" type="button" disabled={isBusy || !id} onClick={() => void review(application, 'request_changes')}>Request changes</button>
                <button className="button danger" type="button" disabled={isBusy || !id} onClick={() => void review(application, 'reject')}>Reject</button>
                <button className="button secondary" type="button" disabled={isBusy || application.status !== 'approved'} onClick={() => void syncAccess(application)}>Sync access</button>
              </div>
            </article>
          );
        })}
        {applications.length === 0 ? <div className="card muted">Нет заявок под текущий фильтр.</div> : null}
      </section>
    </div>
  );
}
