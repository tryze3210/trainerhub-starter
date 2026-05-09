'use client';

import Link from 'next/link';
import { FormEvent, useEffect, useMemo, useState } from 'react';

import {
  createTrainerPayoutRequest,
  getTrainerPayoutBalance,
  listTrainerPayoutRequests,
  type TrainerPayoutListResponse,
  type TrainerPayoutRequest,
  type TrainerPayoutWallet,
} from '@/modules/trainer-payouts/api';

type State = {
  wallet: TrainerPayoutWallet | null;
  payouts: TrainerPayoutListResponse | null;
};

function money(value: string | number | null | undefined, currency = 'RUB') {
  const amount = Number(value ?? 0);
  return new Intl.NumberFormat('ru-RU', {
    style: 'currency',
    currency,
    maximumFractionDigits: 2,
  }).format(Number.isFinite(amount) ? amount : 0);
}

function dateTime(value: string | null | undefined) {
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

function statusHint(payout: TrainerPayoutRequest) {
  if (payout.status === 'rejected') return payout.rejected_reason || 'Отклонена администратором';
  if (payout.status === 'paid') return `Выплачено: ${dateTime(payout.processed_at)}`;
  if (payout.status === 'approved') return `Одобрено: ${dateTime(payout.approved_at)}`;
  if (payout.status === 'processing') return 'Выплата находится в обработке';
  return 'Ожидает проверки администратором';
}

export function TrainerPayoutRequestDashboard() {
  const [state, setState] = useState<State>({ wallet: null, payouts: null });
  const [amount, setAmount] = useState('');
  const [destinationMasked, setDestinationMasked] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const load = () => {
    setIsLoading(true);
    setError(null);
    Promise.all([getTrainerPayoutBalance(), listTrainerPayoutRequests(50)])
      .then(([wallet, payouts]) => setState({ wallet, payouts }))
      .catch((err: unknown) => setError(err instanceof Error ? err.message : 'Не удалось загрузить payout-заявки'))
      .finally(() => setIsLoading(false));
  };

  useEffect(() => {
    load();
  }, []);

  const wallet = state.wallet;
  const currency = wallet?.currency ?? 'RUB';
  const canSubmit = useMemo(() => {
    if (!wallet) return false;
    const requested = Number(amount || 0);
    const minimum = Number(wallet.minimum_payout_amount || 0);
    const available = Number(wallet.available_amount || 0);
    return wallet.can_request_payout && requested >= minimum && requested <= available && destinationMasked.trim().length >= 4;
  }, [amount, destinationMasked, wallet]);

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!canSubmit) return;
    setIsSubmitting(true);
    setError(null);
    setSuccess(null);
    try {
      const response = await createTrainerPayoutRequest({
        amount,
        destination_masked: destinationMasked.trim(),
      });
      setState((current) => ({
        wallet: response.wallet,
        payouts: current.payouts
          ? { ...current.payouts, count: current.payouts.count + 1, results: [response.payout, ...current.payouts.results] }
          : { count: 1, limit: 50, results: [response.payout] },
      }));
      setAmount('');
      setDestinationMasked('');
      setSuccess('Payout-заявка создана и отправлена администратору на проверку.');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось создать payout-заявку');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isLoading && !wallet) {
    return <section className="card">Загружаем payout flow…</section>;
  }

  return (
    <section className="stack gap-lg">
      {error ? <div className="card danger">{error}</div> : null}
      {success ? <div className="card success">{success}</div> : null}

      <div className="grid-4">
        <MetricCard label="Available payout" value={money(wallet?.available_amount, currency)} hint="можно запросить к выплате" />
        <MetricCard label="Reserved / locked" value={money(wallet?.locked_amount, currency)} hint="заявки в обработке и risk holds" />
        <MetricCard label="Lifetime earned" value={money(wallet?.lifetime_earned_amount, currency)} />
        <MetricCard label="Minimum payout" value={money(wallet?.minimum_payout_amount, currency)} />
      </div>

      <div className="grid-2">
        <article className="card stack">
          <h2>Запросить выплату</h2>
          <p className="muted">
            Сумма резервируется из available balance. После approve/processing/paid админом она уйдёт из locked balance.
          </p>
          <form className="stack" onSubmit={submit}>
            <label className="field">
              Сумма
              <input
                type="number"
                min={wallet?.minimum_payout_amount ?? '0'}
                max={wallet?.available_amount ?? undefined}
                step="0.01"
                value={amount}
                onChange={(event) => setAmount(event.target.value)}
                placeholder="500.00"
              />
            </label>
            <label className="field">
              Куда выплатить, только маскированные данные
              <input
                value={destinationMasked}
                onChange={(event) => setDestinationMasked(event.target.value)}
                placeholder="Bank card **** 4242 / SBP **** 0199"
              />
            </label>
            {!wallet?.can_request_payout ? (
              <p className="muted">Available balance меньше минимальной суммы выплаты.</p>
            ) : null}
            <button className="btn primary" type="submit" disabled={!canSubmit || isSubmitting}>
              {isSubmitting ? 'Создаём заявку…' : 'Создать payout-заявку'}
            </button>
          </form>
        </article>

        <article className="card stack">
          <h2>Как работает payout flow</h2>
          <ol className="stack gap-xs">
            <li>Тренер создаёт payout request.</li>
            <li>Сумма переносится из available в locked.</li>
            <li>Админ проверяет risk holds и реквизиты.</li>
            <li>Админ approve → processing → paid или reject.</li>
            <li>При reject сумма возвращается в available balance.</li>
          </ol>
          <Link className="btn ghost" href="/trainer/dashboard/revenue">
            Вернуться к revenue dashboard
          </Link>
        </article>
      </div>

      <article className="card stack">
        <div className="row between wrap gap-md">
          <h2>Payout requests</h2>
          <button className="btn ghost" type="button" onClick={load} disabled={isLoading}>
            Обновить
          </button>
        </div>
        <div className="table-wrap">
          <table className="table">
            <thead>
              <tr>
                <th>Дата</th>
                <th>Amount</th>
                <th>Status</th>
                <th>Destination</th>
                <th>Lifecycle</th>
              </tr>
            </thead>
            <tbody>
              {(state.payouts?.results ?? []).map((payout) => (
                <tr key={payout.id}>
                  <td>{dateTime(payout.created_at)}</td>
                  <td>{money(payout.amount, payout.currency)}</td>
                  <td><span className="badge">{payout.status}</span></td>
                  <td>{payout.destination_masked || '—'}</td>
                  <td>{statusHint(payout)}</td>
                </tr>
              ))}
              {(state.payouts?.results ?? []).length === 0 ? (
                <tr>
                  <td colSpan={5}>Payout-заявок пока нет.</td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </article>
    </section>
  );
}
