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
  if (!value) return 'Дата не указана';
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

function sourceLabel(value?: string | null) {
  const source = (value || '').toLowerCase();
  if (source === 'product') return 'Продукт';
  if (source === 'course') return 'Курс';
  if (source === 'video') return 'Видео';
  if (source === 'subscription') return 'Подписка';
  if (source === 'order') return 'Заказ';
  if (source === 'manual') return 'Ручная операция';
  return 'Источник дохода';
}

function directionLabel(value?: string | null) {
  const direction = (value || '').toLowerCase();
  if (direction === 'credit' || direction === 'incoming') return 'Поступление';
  if (direction === 'debit' || direction === 'outgoing') return 'Списание';
  if (direction === 'hold') return 'Резерв';
  if (direction === 'reversal') return 'Возврат резерва';
  return 'Операция';
}

function statusLabel(value?: string | null) {
  const status = (value || '').toLowerCase();
  if (status === 'posted' || status === 'paid' || status === 'completed' || status === 'success') return 'Проведено';
  if (status === 'pending' || status === 'processing') return 'В обработке';
  if (status === 'approved') return 'Одобрено';
  if (status === 'rejected') return 'Отклонено';
  if (status === 'failed' || status === 'error') return 'Ошибка';
  if (status === 'cancelled') return 'Отменено';
  return 'Требуется проверка';
}

function statusTone(value?: string | null) {
  const status = (value || '').toLowerCase();
  if (['posted', 'paid', 'completed', 'success', 'approved'].includes(status)) return 'success';
  if (['pending', 'processing', 'hold'].includes(status)) return 'warning';
  if (['rejected', 'failed', 'error', 'cancelled'].includes(status)) return 'danger';
  return 'neutral';
}

function statusClass(value?: string | null) {
  return `trainer-finance-status trainer-finance-status-${statusTone(value)}`;
}

function KpiCard({ label, value, hint }: { label: string; value: string | number; hint?: string }) {
  return (
    <article className="trainer-finance-kpi-card">
      <span>{label}</span>
      <strong>{value}</strong>
      {hint ? <small>{hint}</small> : null}
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
          setError(err instanceof Error ? err.message : 'Не удалось загрузить финансы тренера');
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
  const maxRevenueOrigin = useMemo(() => {
    const amounts = summary?.top_sources.map((item) => Number(item.net_revenue)) ?? [];
    return Math.max(...amounts, 1);
  }, [summary]);

  if (isLoading && !summary) {
    return (
      <section className="trainer-finance-workbench">
        <div className="trainer-finance-message">
          <strong>Загружаем финансы</strong>
          <p>Собираем баланс, комиссии, операции и заявки на выплаты.</p>
        </div>
      </section>
    );
  }

  if (error) {
    return (
      <section className="trainer-finance-workbench">
        <div className="trainer-finance-message">
          <strong>Финансы недоступны</strong>
          <p>{error}</p>
        </div>
      </section>
    );
  }

  if (!summary) {
    return (
      <section className="trainer-finance-workbench">
        <div className="trainer-finance-empty">
          <strong>Финансовых данных пока нет</strong>
          <p>Когда появятся продажи или выплаты, баланс и операции будут показаны здесь.</p>
        </div>
      </section>
    );
  }

  return (
    <section className="trainer-finance-workbench">
      <section className="trainer-finance-hero">
        <div>
          <h2>Финансы</h2>
          <p>Баланс, комиссии, выплаты и движение средств.</p>
        </div>
        <div className="trainer-finance-hero-total">
          <span>Доступно к выплате</span>
          <strong>{money(summary.revenue.available_payout, currency)}</strong>
          <small>{summary.trainer.display_name} · период {summary.period.days} дней</small>
        </div>
      </section>

      <section className="trainer-finance-toolbar" aria-label="Фильтры финансов">
        <label className="trainer-finance-field">
          <span>Период</span>
          <select value={days} onChange={(event) => setDays(Number(event.target.value))}>
            <option value={7}>7 дней</option>
            <option value={30}>30 дней</option>
            <option value={90}>90 дней</option>
            <option value={365}>365 дней</option>
          </select>
        </label>
        <Link className="premium-secondary-button" href="/trainer/dashboard/payouts">Запросить выплату</Link>
      </section>

      <section className="trainer-finance-kpi-grid" aria-label="Финансовые показатели">
        <KpiCard label="Доступно к выплате" value={money(summary.revenue.available_payout, currency)} />
        <KpiCard label="Чистая выручка" value={money(summary.revenue.net_revenue, currency)} />
        <KpiCard label="Валовая выручка" value={money(summary.revenue.gross_sales, currency)} />
        <KpiCard label="Комиссия платформы" value={money(summary.revenue.platform_commission, currency)} />
        <KpiCard label="В обработке" value={money(summary.revenue.pending_payout, currency)} />
      </section>

      <section className="trainer-finance-workspace">
        <div className="trainer-finance-main">
          <article className="trainer-finance-panel">
            <h3>Wallet cockpit</h3>
            <div className="trainer-finance-kpi-grid">
              <KpiCard label="Доступный баланс" value={money(summary.wallet.available_amount, currency)} />
              <KpiCard label="Ожидает подтверждения" value={money(summary.wallet.pending_amount, currency)} />
              <KpiCard label="Заблокировано" value={money(summary.wallet.locked_amount, currency)} />
              <KpiCard label="Всего заработано" value={money(summary.wallet.lifetime_earned, currency)} />
            </div>
            <div className="trainer-finance-row">
              <span className="trainer-finance-muted">Ближайшее действие</span>
              <Link className="premium-secondary-button" href="/trainer/dashboard/payouts">Открыть выплаты</Link>
            </div>
          </article>

          <article className="trainer-finance-panel">
            <h3>Источники дохода</h3>
            {summary.top_sources.length === 0 ? (
              <div className="trainer-finance-empty">
                <strong>Источников дохода пока нет</strong>
                <p>Опубликуйте продукт или видео, чтобы увидеть доход по материалам.</p>
              </div>
            ) : (
              <div className="trainer-finance-rail" aria-label="Источники дохода">
                {summary.top_sources.map((item, index) => {
                  const width = Math.max(6, (Number(item.net_revenue) / maxRevenueOrigin) * 100);
                  return (
                    <article className="trainer-finance-source-card" key={`${item.source_type}:${item.source_id ?? index}`}>
                      <strong>{sourceLabel(item.source_type)}</strong>
                      <span>{money(item.net_revenue, currency)}</span>
                      <small>{item.transaction_count} операций</small>
                      <div className="trainer-analytics-progress"><span style={{ width: `${width}%` }} /></div>
                    </article>
                  );
                })}
              </div>
            )}
          </article>

          <article className="trainer-finance-panel">
            <h3>Движение средств</h3>
            <div className="trainer-finance-timeline">
              {(state.transactions?.results ?? []).map((entry) => (
                <article className="trainer-finance-timeline-item" key={entry.id}>
                  <div className="trainer-finance-row">
                    <div>
                      <strong>{directionLabel(entry.direction)}</strong>
                      <span className="trainer-finance-muted">{sourceLabel(entry.source_type)} · {dateTime(entry.created_at)}</span>
                    </div>
                    <span className={statusClass(entry.status)}>{statusLabel(entry.status)}</span>
                  </div>
                  <div className="trainer-finance-row">
                    <span>{entry.description || 'Финансовая операция'}</span>
                    <strong>{money(entry.amount, entry.currency)}</strong>
                  </div>
                </article>
              ))}
              {!state.transactions?.results.length ? (
                <div className="trainer-finance-empty">
                  <strong>Операций пока нет</strong>
                  <p>Движение средств появится после продаж, возвратов или выплат.</p>
                </div>
              ) : null}
            </div>
          </article>
        </div>

        <aside className="trainer-finance-sidebar">
          <article className="trainer-finance-panel">
            <h3>Заявки на выплаты</h3>
            <div className="trainer-finance-timeline">
              {(state.payouts?.results ?? []).map((payout) => (
                <article className="trainer-finance-compact-card" key={payout.id}>
                  <div className="trainer-finance-row">
                    <strong>{money(payout.amount, payout.currency)}</strong>
                    <span className={statusClass(payout.status)}>{statusLabel(payout.status)}</span>
                  </div>
                  <span>{dateTime(payout.created_at)}</span>
                  <small className="trainer-finance-muted">{payout.destination_masked || 'Метод выплаты не указан'}</small>
                  {payout.rejected_reason ? <small>{payout.rejected_reason}</small> : null}
                </article>
              ))}
              {!state.payouts?.results.length ? (
                <div className="trainer-finance-empty">
                  <strong>Заявок пока нет</strong>
                  <p>Когда вы запросите выплату, её статус появится здесь.</p>
                </div>
              ) : null}
            </div>
          </article>

          <article className="trainer-finance-panel">
            <h3>Финансовые сигналы</h3>
            <div className="trainer-finance-timeline">
              <div className="trainer-finance-compact-card">
                <span className="trainer-finance-muted">В резерве</span>
                <strong>{money(summary.revenue.reserved_balance, currency)}</strong>
              </div>
              <div className="trainer-finance-compact-card">
                <span className="trainer-finance-muted">Возвраты</span>
                <strong>{money(summary.revenue.refunds, currency)}</strong>
              </div>
              <div className="trainer-finance-compact-card">
                <span className="trainer-finance-muted">Споры</span>
                <strong>{money(summary.revenue.chargebacks, currency)}</strong>
              </div>
              {summary.notes.map((note) => <p className="trainer-finance-muted" key={note}>{note}</p>)}
            </div>
          </article>
        </aside>
      </section>
    </section>
  );
}
