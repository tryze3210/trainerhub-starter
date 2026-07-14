'use client';

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import { ProtectedPage } from '@/components/protected-page';
import { adminAuditApi, type AuditEvent } from '@/modules/admin-audit/api';
import { useAuthSession } from '@/components/auth-provider';
import { isAdminUser } from '@/lib/authz';
import {
  downloadReferralAdminCsv,
  referralsAdminApi,
  type ReferralAdminAttribution,
  type ReferralAdminInvite,
  type ReferralAdminExportKind,
  type ReferralAdminLedgerEntry,
  type ReferralAdminOpsOverview,
  type ReferralAdminReward,
  type ReferralMoney,
} from '@/modules/referrals/api';

function formatDate(value?: string | null) {
  if (!value) return '—';

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;

  return new Intl.DateTimeFormat('ru-RU', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(date);
}

function money(value?: ReferralMoney, currency = 'RUB') {
  if (value === undefined || value === null || value === '') return `0 ${currency}`;
  return `${value} ${currency}`;
}

function statusBadge(status?: string | null) {
  if (status === 'approved' || status === 'paid' || status === 'converted') return 'badge success';
  if (status === 'rejected' || status === 'failed' || status === 'cancelled') return 'badge danger';
  if (status === 'pending' || status === 'created') return 'badge warning';
  return 'badge secondary';
}

function metric(totals: Record<string, string | number | null | undefined> | undefined, ...keys: string[]) {
  for (const key of keys) {
    const value = totals?.[key];
    if (value !== undefined && value !== null && value !== '') return value;
  }

  return 0;
}

function rewardAmount(item: ReferralAdminReward) {
  return item.reward_amount ?? item.amount;
}

function shortId(value?: string | null) {
  if (!value) return '—';
  return value.length > 12 ? `${value.slice(0, 8)}…${value.slice(-4)}` : value;
}

function exportKindLabel(value?: string | null) {
  if (!value) return 'export';
  if (value === 'rewards') return 'Rewards CSV';
  if (value === 'ledger') return 'Ledger CSV';
  if (value === 'invites') return 'Invites CSV';
  return `${value} CSV`;
}

function exportRowsLabel(event: AuditEvent) {
  const context = event.context?.context || {};
  const exportedRows = context.exported_rows;
  const totalRows = context.total_rows;
  const truncated = context.truncated;

  if (exportedRows === undefined && totalRows === undefined) return 'rows —';

  const exported = exportedRows === undefined ? '—' : String(exportedRows);
  const total = totalRows === undefined ? '—' : String(totalRows);
  return `${exported}/${total}${truncated ? ' · truncated' : ''}`;
}

function ExportAuditList({ events }: { events: AuditEvent[] }) {
  if (!events.length) {
    return <p className="muted">Событий аудита CSV-выгрузок пока нет.</p>;
  }

  return (
    <div className="stack" style={{ gap: 10 }}>
      {events.slice(0, 6).map((event) => {
        const context = event.context?.context || {};
        const kind = typeof context.export_kind === 'string' ? context.export_kind : event.entity_id;
        const filename = typeof context.filename === 'string' ? context.filename : '';

        return (
          <div className="list-item" key={event.id}>
            <div className="row">
              <div>
                <strong>{exportKindLabel(kind)}</strong>
                <small style={{ display: 'block', marginTop: 4 }}>{filename || 'filename —'}</small>
              </div>
              <span className="badge secondary">{exportRowsLabel(event)}</span>
            </div>
            <small>
              {formatDate(event.created_at)} · {event.actor_email || 'system/admin'} · {event.ip_address || 'ip —'}
            </small>
          </div>
        );
      })}
    </div>
  );
}

function RewardsTable({ rewards }: { rewards: ReferralAdminReward[] }) {
  if (!rewards.length) {
    return <p className="muted">Событий вознаграждений под выбранные фильтры нет.</p>;
  }

  return (
    <div className="table-wrap">
      <table className="table">
        <thead>
          <tr>
            <th>Статус</th>
            <th>Программа</th>
            <th>Сумма</th>
            <th>Триггер</th>
            <th>Владелец</th>
            <th>Создано</th>
          </tr>
        </thead>
        <tbody>
          {rewards.slice(0, 25).map((reward) => (
            <tr key={reward.id}>
              <td><span className={statusBadge(reward.status)}>{reward.status || '—'}</span></td>
              <td>{reward.program_slug || '—'}</td>
              <td>{money(rewardAmount(reward), reward.currency || 'RUB')}</td>
              <td>{reward.trigger_type || '—'} · {shortId(reward.trigger_reference)}</td>
              <td>{reward.owner_email || shortId(reward.owner_id)}</td>
              <td>{formatDate(reward.created_at)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function LedgerList({ entries }: { entries: ReferralAdminLedgerEntry[] }) {
  if (!entries.length) {
    return <p className="muted">Записей реестра под выбранные фильтры нет.</p>;
  }

  return (
    <div className="stack" style={{ gap: 10 }}>
      {entries.slice(0, 10).map((entry) => (
        <div className="list-item" key={entry.id}>
          <div className="row">
            <div>
              <span className="badge secondary">{entry.entry_type || 'entry'}</span>
              <strong style={{ display: 'block', marginTop: 8 }}>{money(entry.amount, entry.currency || 'RUB')}</strong>
            </div>
            <small>{formatDate(entry.created_at)}</small>
          </div>
          <small>reward {shortId(entry.reward_id || entry.reward)} · {entry.reason || '—'}</small>
        </div>
      ))}
    </div>
  );
}

function InvitesList({ invites }: { invites: ReferralAdminInvite[] }) {
  if (!invites.length) {
    return <p className="muted">Событий приглашений под выбранные фильтры нет.</p>;
  }

  return (
    <div className="stack" style={{ gap: 10 }}>
      {invites.slice(0, 8).map((invite) => (
        <div className="list-item" key={invite.id}>
          <div className="row">
            <strong>{invite.referral_code || invite.code || shortId(invite.id)}</strong>
            <span className={statusBadge(invite.status)}>{invite.status || '—'}</span>
          </div>
          <small>
            {invite.program_slug || 'program —'} · {invite.landing_path || '/'} · created {formatDate(invite.created_at)}
          </small>
        </div>
      ))}
    </div>
  );
}

function AttributionsList({ attributions }: { attributions: ReferralAdminAttribution[] }) {
  if (!attributions.length) {
    return <p className="muted">Записей атрибуции под выбранные фильтры нет.</p>;
  }

  return (
    <div className="stack" style={{ gap: 10 }}>
      {attributions.slice(0, 8).map((item) => (
        <div className="list-item" key={item.id}>
          <div className="row">
            <strong>{item.referral_code || item.code || shortId(item.id)}</strong>
            <span className={statusBadge(item.status)}>{item.status || '—'}</span>
          </div>
          <small>
            referred {shortId(item.referred_user_id)} · source {item.source || '—'} · {formatDate(item.created_at)}
          </small>
        </div>
      ))}
    </div>
  );
}

export default function AdminРефералыPage() {
  const { user } = useAuthSession();
  const isAdmin = isAdminUser(user);

  const [days, setDays] = useState(30);
  const [statusFilter, setStatusFilter] = useState('');
  const [programSlug, setProgramSlug] = useState('');
  const [search, setSearch] = useState('');
  const [overview, setOverview] = useState<ReferralAdminOpsOverview | null>(null);
  const [rewards, setRewards] = useState<ReferralAdminReward[]>([]);
  const [ledger, setLedger] = useState<ReferralAdminLedgerEntry[]>([]);
  const [invites, setInvites] = useState<ReferralAdminInvite[]>([]);
  const [attributions, setAttributions] = useState<ReferralAdminAttribution[]>([]);
  const [msg, setMsg] = useState('');
  const [exporting, setExporting] = useState<ReferralAdminExportKind | ''>('');
  const [exportMsg, setExportMsg] = useState('');
  const [exportAuditEvents, setExportAuditEvents] = useState<AuditEvent[]>([]);

  const query = useMemo(() => ({
    status: statusFilter || undefined,
    program_slug: programSlug || undefined,
    search: search || undefined,
  }), [programSlug, search, statusFilter]);

  async function load() {
    try {
      setMsg('');
      const [overviewPayload, rewardsPayload, ledgerPayload, invitesPayload, attributionsPayload, exportAuditPayload] = await Promise.all([
        referralsAdminApi.getOpsOverview(days),
        referralsAdminApi.listRewards(query),
        referralsAdminApi.listLedger(query),
        referralsAdminApi.listInvites(query),
        referralsAdminApi.listAttributions(query),
        adminAuditApi.listEvents({
          event_type: 'admin.referrals.csv_export',
          entity_type: 'referral_export',
          limit: 25,
        }),
      ]);

      setOverview(overviewPayload);
      setRewards(rewardsPayload);
      setLedger(ledgerPayload);
      setInvites(invitesPayload);
      setAttributions(attributionsPayload);
      setExportAuditEvents(exportAuditPayload);
    } catch (err) {
      setMsg(err instanceof Error ? err.message : 'Не удалось загрузить referral ops');
    }
  }

  useEffect(() => {
    if (!isAdmin) return;
    void load();
  }, [days, isAdmin, query]);


  async function handleExport(kind: ReferralAdminExportKind) {
    try {
      setExporting(kind);
      setExportMsg('');
      const filename = await downloadReferralAdminCsv(kind, query);
      setExportMsg(`CSV export готов: ${filename}`);
      const exportAuditPayload = await adminAuditApi.listEvents({
        event_type: 'admin.referrals.csv_export',
        entity_type: 'referral_export',
        limit: 25,
      });
      setExportAuditEvents(exportAuditPayload);
    } catch (err) {
      setExportMsg(err instanceof Error ? err.message : 'Не удалось выгрузить CSV');
    } finally {
      setExporting('');
    }
  }

  const totals = overview?.totals;
  const integrity = overview?.integrity;
  const issueCount = Number(integrity?.issue_count || 0);

  return (
    <ProtectedPage
      title="Реферальные операции"
      description="Админское управление амбассадорской атрибуцией, вознаграждениями и реферальным реестром."
    >
      {!isAdmin ? (
        <div className="card error">У текущей сессии нет роли администратора.</div>
      ) : (
        <section className="stack" style={{ gap: 24 }}>
          <div className="card hero">
            <div className="row">
              <div>
                <span className="badge secondary">Рост и рефералы</span>
                <h1 style={{ marginTop: 12 }}>Реферальные операции</h1>
                <p className="lead">
                  Attribution, invite conversion, reward начисления, ledger entries и integrity snapshot в одном admin workflow.
                </p>
              </div>
              <button className="button secondary" onClick={() => void load()}>Обновить</button>
            </div>
          </div>

          {msg ? <div className="card error">{msg}</div> : null}

          <div className="grid-4">
            <div className="card kpi">
              <span className="muted">Приглашения</span>
              <strong>{metric(totals, 'invites', 'total_invites', 'invite_count')}</strong>
              <small>за {overview?.window_days || overview?.days || days} дней</small>
            </div>
            <div className="card kpi">
              <span className="muted">Атрибуции</span>
              <strong>{metric(totals, 'attributions', 'total_attributions', 'attribution_count')}</strong>
              <small>привязки регистраций</small>
            </div>
            <div className="card kpi">
              <span className="muted">Одобренные вознаграждения</span>
              <strong>{money(metric(totals, 'approved_reward_amount', 'approved_rewards_amount', 'rewards_amount'))}</strong>
              <small>{metric(totals, 'approved_rewards', 'approved_reward_count', 'rewards_count')} rewards</small>
            </div>
            <div className={`card kpi ${issueCount ? 'warning' : 'success'}`}>
              <span className="muted">Целостность</span>
              <strong>{issueCount}</strong>
              <small>{issueCount ? 'issues need review' : 'healthy snapshot'}</small>
            </div>
          </div>

          <div className="card">
            <h2 className="title-md">Фильтры</h2>
            <div className="form-row" style={{ marginTop: 16 }}>
              <label className="form-group">
                <span className="label">Период</span>
                <select className="select" value={days} onChange={(event) => setDays(Number(event.target.value))}>
                  <option value={7}>7 дней</option>
                  <option value={30}>30 дней</option>
                  <option value={90}>90 дней</option>
                  <option value={180}>180 дней</option>
                </select>
              </label>
              <label className="form-group">
                <span className="label">Статус</span>
                <select className="select" value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>
                  <option value="">Все</option>
                  <option value="pending">Ожидает</option>
                  <option value="created">Создано</option>
                  <option value="converted">Конвертировано</option>
                  <option value="approved">Одобрено</option>
                  <option value="rejected">Отклонено</option>
                  <option value="paid">Оплачено</option>
                </select>
              </label>
              <label className="form-group">
                <span className="label">Код программы</span>
                <input className="input" value={programSlug} onChange={(event) => setProgramSlug(event.target.value)} placeholder="ambassador" />
              </label>
              <label className="form-group">
                <span className="label">Поиск</span>
                <input className="input" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="код, email, ссылка триггера" />
              </label>
            </div>
          </div>


          <div className="card">
            <div className="row">
              <div>
                <h2 className="title-md">CSV-выгрузки</h2>
                <p className="muted">Выгрузка вознаграждений, реестра и приглашений с текущими фильтрами. Backend ограничивает экспорт 10 000 строками.</p>
              </div>
              {exportMsg ? <span className="badge secondary">{exportMsg}</span> : null}
            </div>
            <div className="form-row" style={{ marginTop: 16 }}>
              <button className="button secondary" disabled={Boolean(exporting)} onClick={() => void handleExport('rewards')}>
                {exporting === 'rewards' ? 'Выгружаю rewards…' : 'Rewards CSV'}
              </button>
              <button className="button secondary" disabled={Boolean(exporting)} onClick={() => void handleExport('ledger')}>
                {exporting === 'ledger' ? 'Выгружаю ledger…' : 'Ledger CSV'}
              </button>
              <button className="button secondary" disabled={Boolean(exporting)} onClick={() => void handleExport('invites')}>
                {exporting === 'invites' ? 'Выгружаю invites…' : 'Invites CSV'}
              </button>
            </div>
          </div>

          <div className="card">
            <div className="row">
              <div>
                <h2 className="title-md">Последний аудит CSV-выгрузок</h2>
                <p className="muted">Последние события аудита по реферальным выгрузкам. Используется тот же журнал аудита, что и в операционном контуре.</p>
              </div>
              <Link
                className="button secondary"
                href="/admin/audit"
              >
                Открыть общий Журнал аудита
              </Link>
            </div>
            <div style={{ marginTop: 16 }}>
              <ExportAuditList events={exportAuditEvents} />
            </div>
          </div>

          <div className="grid-2">
            <div className="card">
              <h2 className="title-md">Снимок целостности</h2>
              <div className="grid-2" style={{ marginTop: 16 }}>
                <div className="list-item"><span className="muted">Просроченные ожидающие приглашения</span><strong>{integrity?.stale_pending_invites || 0}</strong></div>
                <div className="list-item"><span className="muted">Конверсии без атрибуции</span><strong>{integrity?.converted_invites_without_attribution || 0}</strong></div>
                <div className="list-item"><span className="muted">Одобрено без реестра</span><strong>{integrity?.approved_rewards_without_ledger || 0}</strong></div>
                <div className="list-item"><span className="muted">Дубликаты реестра вознаграждений</span><strong>{integrity?.rewards_with_multiple_ledger_entries || 0}</strong></div>
              </div>
            </div>

            <div className="card">
              <h2 className="title-md">Группы статусов вознаграждений</h2>
              <div className="stack" style={{ gap: 10, marginTop: 16 }}>
                {(overview?.rewards_by_status || []).length === 0 ? <p className="muted">Групп данных пока нет.</p> : null}
                {(overview?.rewards_by_status || []).map((bucket, index) => (
                  <div className="list-item" key={`${bucket.status}-${index}`}>
                    <div className="row">
                      <span className={statusBadge(bucket.status)}>{bucket.status || '—'}</span>
                      <strong>{bucket.count || 0}</strong>
                    </div>
                    <small>{money(bucket.amount ?? bucket.reward_amount, bucket.currency || 'RUB')}</small>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="card">
            <div className="row">
              <div>
                <h2 className="title-md">Вознаграждения</h2>
                <p className="muted">Последние события вознаграждений после оплаты заказа или триггера конверсии.</p>
              </div>
              <span className="badge secondary">{rewards.length}</span>
            </div>
            <div style={{ marginTop: 16 }}>
              <RewardsTable rewards={rewards} />
            </div>
          </div>

          <div className="grid-2">
            <div className="card">
              <h2 className="title-md">Реестр</h2>
              <div style={{ marginTop: 16 }}><LedgerList entries={ledger} /></div>
            </div>
            <div className="card">
              <h2 className="title-md">Приглашения</h2>
              <div style={{ marginTop: 16 }}><InvitesList invites={invites} /></div>
            </div>
          </div>

          <div className="card">
            <h2 className="title-md">Атрибуции</h2>
            <div style={{ marginTop: 16 }}><AttributionsList attributions={attributions} /></div>
          </div>
        </section>
      )}
    </ProtectedPage>
  );
}
