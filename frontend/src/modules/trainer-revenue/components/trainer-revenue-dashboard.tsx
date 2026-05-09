'use client';

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';

import {
  getTrainerRevenuePayouts,
  getTrainerRevenueSummary,
  getTrainerRevenueTransactions,
  type TrainerRevenueListResponse,
  type TrainerRevenuePayout,
  type TrainerRevenueSummary,
  type TrainerRevenueTransaction,
} from '@/modules/trainer-revenue/api';

type DashboardState = {
  summary: TrainerRevenueSummary | null;
  transactions: TrainerRevenueListResponse<TrainerRevenueTransaction> | null;
  payouts: TrainerRevenueListResponse<TrainerRevenuePayout> | null;
};

function money(value: string | number | null | undefined, currency = 'RUB') {
  const amount = Number(value ?? 0);
  return new Intl.NumberFormat('ru-RU', {
    style: 'currency',
    currency,
    maximumFractionDigits: 2,
  }).format(Number.isFinite(amount) ? amount : 0);
}

function dateTime(value: string | null) {
  if (!value) return '—';
  return new Intl.DateTimeFormat('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value));
}

function MetricCard({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <article className="card stack">
      <span className="muted">{label}</span>
      <strong className="stat-value">{value}</strong>
      {hint ? <span className="muted">{hint}</span> : null}
    </article>
  );
}

export function TrainerRevenueDashboard() {
  const [days, setDays] = useState(30);
  const [state, setState] = useState<DashboardState>({ summary: null, transactions: null, payouts: null });
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setIsLoading(true);
    setError(null);

    Promise.all([
      getTrainerRevenueSummary(days),
      getTrainerRevenueTransactions(50),
      getTrainerRevenuePayouts(50),
    ])
      .then(([summary, transactions, payouts]) => {
        if (!cancelled) {
          setState({ summary, transactions, payouts });
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Не удалось загрузить доходы тренера');
        }
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [days]);

  const summary = state.summary;
  const currency = summary?.currency ?? 'RUB';
  const maxTopSource = useMemo(() => {
    const amounts = summary?.top_sources.map((item) => Number(item.net_revenue)) ?? [];
    return Math.max(...amounts, 1);
  }, [summary]);

  if (isLoading && !summary) {
    return <section className="card">Загружаем revenue dashboard…</section>;
  }

  if (error) {
    return (
      <section className="card stack">
        <h2>Revenue dashboard недоступен</h2>
        <p className="muted">{error}</p>
      </section>
    );
  }

  if (!summary) {
    return <section className="card">Нет данных по доходам.</section>;
  }

  return (
    <section className="stack gap-lg">
      <div className="card row between wrap gap-md">
        <div>
          <h2>Доходы тренера</h2>
          <p className="muted">
            {summary.trainer.display_name} · {summary.trainer.status} · период {summary.period.days} дней
          </p>
        </div>
        <div className="row wrap gap-sm">
          <Link className="btn primary" href="/trainer/dashboard/payouts">
            Запросить выплату
          </Link>
          <label className="field-inline">
            Период
            <select value={days} onChange={(event) => setDays(Number(event.target.value))}>
              <option value={7}>7 дней</option>
              <option value={30}>30 дней</option>
              <option value={90}>90 дней</option>
              <option value={365}>365 дней</option>
            </select>
          </label>
        </div>
      </div>

      <div className="grid-4">
        <MetricCard label="Net revenue" value={money(summary.revenue.net_revenue, currency)} hint="доход тренера после комиссии" />
        <MetricCard label="Estimated gross sales" value={money(summary.revenue.gross_sales, currency)} hint="оценка до комиссии" />
        <MetricCard label="Platform commission" value={money(summary.revenue.platform_commission, currency)} />
        <MetricCard label="Available payout" value={money(summary.revenue.available_payout, currency)} />
      </div>

      <div className="grid-4">
        <MetricCard label="Pending payout" value={money(summary.revenue.pending_payout, currency)} />
        <MetricCard label="Reserved / locked" value={money(summary.revenue.reserved_balance, currency)} />
        <MetricCard label="Refunds" value={money(summary.revenue.refunds, currency)} />
        <MetricCard label="Chargebacks" value={money(summary.revenue.chargebacks, currency)} />
      </div>

      <div className="grid-2">
        <article className="card stack">
          <h3>Wallet</h3>
          <dl className="details-list">
            <div><dt>Available</dt><dd>{money(summary.wallet.available_amount, currency)}</dd></div>
            <div><dt>Pending</dt><dd>{money(summary.wallet.pending_amount, currency)}</dd></div>
            <div><dt>Locked</dt><dd>{money(summary.wallet.locked_amount, currency)}</dd></div>
            <div><dt>Lifetime earned</dt><dd>{money(summary.wallet.lifetime_earned, currency)}</dd></div>
          </dl>
        </article>

        <article className="card stack">
          <h3>Top revenue sources</h3>
          {summary.top_sources.length === 0 ? (
            <p className="muted">Продаж за выбранный период пока нет.</p>
          ) : (
            <div className="stack">
              {summary.top_sources.map((item) => {
                const width = Math.max(6, (Number(item.net_revenue) / maxTopSource) * 100);
                return (
                  <div key={`${item.source_type}:${item.source_id ?? 'none'}`} className="stack gap-xs">
                    <div className="row between gap-md">
                      <span>{item.source_type}</span>
                      <strong>{money(item.net_revenue, currency)}</strong>
                    </div>
                    <div className="progress"><span style={{ width: `${width}%` }} /></div>
                    <span className="muted">{item.transaction_count} transactions · {item.source_id ?? 'no source id'}</span>
                  </div>
                );
              })}
            </div>
          )}
        </article>
      </div>

      <article className="card stack">
        <h3>Recent ledger transactions</h3>
        <div className="table-wrap">
          <table className="table">
            <thead>
              <tr>
                <th>Дата</th>
                <th>Тип</th>
                <th>Direction</th>
                <th>Amount</th>
                <th>Status</th>
                <th>Source</th>
              </tr>
            </thead>
            <tbody>
              {(state.transactions?.results ?? []).map((entry) => (
                <tr key={entry.id}>
                  <td>{dateTime(entry.created_at)}</td>
                  <td>{entry.entry_type}</td>
                  <td><span className="badge">{entry.direction}</span></td>
                  <td>{money(entry.amount, entry.currency)}</td>
                  <td>{entry.status}</td>
                  <td>{entry.source_type}:{entry.source_id ?? '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </article>

      <article className="card stack">
        <h3>Payout requests</h3>
        <div className="table-wrap">
          <table className="table">
            <thead>
              <tr>
                <th>Дата</th>
                <th>Amount</th>
                <th>Status</th>
                <th>Processed at</th>
                <th>Reject reason</th>
              </tr>
            </thead>
            <tbody>
              {(state.payouts?.results ?? []).map((payout) => (
                <tr key={payout.id}>
                  <td>{dateTime(payout.created_at)}</td>
                  <td>{money(payout.amount, payout.currency)}</td>
                  <td><span className="badge">{payout.status}</span></td>
                  <td>{dateTime(payout.processed_at)}</td>
                  <td>{payout.rejected_reason || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </article>

      {summary.notes.length > 0 ? (
        <aside className="card muted">
          {summary.notes.map((note) => <p key={note}>{note}</p>)}
        </aside>
      ) : null}
    </section>
  );
}
