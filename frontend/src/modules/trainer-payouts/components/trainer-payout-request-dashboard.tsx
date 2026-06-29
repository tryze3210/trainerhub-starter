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

function formatMoney(value: string | number | null | undefined, currency = 'RUB') {
  const amount = Number(value ?? 0);
  return new Intl.NumberFormat('ru-RU', {
    style: 'currency',
    currency,
    maximumFractionDigits: 2,
  }).format(Number.isFinite(amount) ? amount : 0);
}

function formatDateTime(value: string | null | undefined) {
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

function mapPayoutStatusLabel(value?: string | null) {
  if (value === 'pending') return 'На проверке';
  if (value === 'approved') return 'Одобрено';
  if (value === 'processing') return 'В обработке';
  if (value === 'paid') return 'Выплачено';
  if (value === 'rejected') return 'Отклонено';
  if (value === 'cancelled') return 'Отменено';
  if (value === 'failed') return 'Ошибка выплаты';
  return 'Требуется проверка';
}

function getBadgeTone(value?: string | null) {
  if (['paid', 'approved'].includes(value || '')) return 'success';
  if (['pending', 'processing'].includes(value || '')) return 'warning';
  if (['rejected', 'cancelled', 'failed'].includes(value || '')) return 'danger';
  return 'neutral';
}

function badgeClass(value?: string | null) {
  return `trainer-education-status trainer-education-status-${getBadgeTone(value)}`;
}

function statusHint(payout: TrainerPayoutRequest) {
  if (payout.status === 'rejected') return payout.rejected_reason || 'Заявка отклонена, сумма возвращается на доступный баланс.';
  if (payout.status === 'paid') return `Средства выплачены: ${formatDateTime(payout.processed_at)}.`;
  if (payout.status === 'approved') return `Заявка одобрена: ${formatDateTime(payout.approved_at)}.`;
  if (payout.status === 'processing') return 'Финансовая команда отправляет выплату.';
  return 'Заявка ожидает проверки реквизитов и рисков.';
}

function KpiCard({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <article className="trainer-education-kpi-card">
      <span>{label}</span>
      <strong>{value}</strong>
      {hint ? <small>{hint}</small> : null}
    </article>
  );
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
      .catch((err: unknown) => setError(err instanceof Error ? err.message : 'Не удалось загрузить заявки на выплаты'))
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
      setSuccess('Заявка на выплату создана и отправлена на проверку.');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось создать заявку на выплату');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isLoading && !wallet) {
    return (
      <section className="trainer-payout-workbench">
        <div className="trainer-education-message">
          <strong>Загружаем выплаты</strong>
          <p>Проверяем баланс, лимиты и историю заявок.</p>
        </div>
      </section>
    );
  }

  return (
    <section className="trainer-payout-workbench">
      <section className="trainer-payout-hero">
        <div>
          <h2>Выплаты</h2>
          <p>Запрос выплаты, резервирование средств и история заявок.</p>
        </div>
        <div className="trainer-education-hero-total">
          <span>Доступно к выплате</span>
          <strong>{formatMoney(wallet?.available_amount, currency)}</strong>
          <small>{formatMoney(wallet?.pending_amount, currency)} в обработке · {formatMoney(wallet?.locked_amount, currency)} заблокировано · {formatMoney(wallet?.lifetime_earned_amount, currency)} заработано всего</small>
        </div>
      </section>

      {error ? <div className="trainer-education-message"><strong>Ошибка выплаты</strong><p>{error}</p></div> : null}
      {success ? <div className="trainer-education-message"><strong>Готово</strong><p>{success}</p></div> : null}

      <section className="trainer-payout-kpi-grid" aria-label="Показатели выплат">
        <KpiCard label="Доступно" value={formatMoney(wallet?.available_amount, currency)} />
        <KpiCard label="В обработке" value={formatMoney(wallet?.pending_amount, currency)} />
        <KpiCard label="Заблокировано" value={formatMoney(wallet?.locked_amount, currency)} />
        <KpiCard label="Заработано всего" value={formatMoney(wallet?.lifetime_earned_amount, currency)} />
        <KpiCard label="Минимальная выплата" value={formatMoney(wallet?.minimum_payout_amount, currency)} />
      </section>

      <section className="trainer-payout-layout">
        <div className="trainer-education-main">
          <article className="trainer-payout-request-card">
            <h3>Новая заявка на выплату</h3>
            <form className="trainer-education-main" onSubmit={submit}>
              <label className="trainer-education-field">
                <span>Сумма выплаты</span>
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
              <label className="trainer-education-field">
                <span>Куда выплатить</span>
                <input
                  value={destinationMasked}
                  onChange={(event) => setDestinationMasked(event.target.value)}
                  placeholder="Карта **** 4242 / СБП **** 0199"
                />
              </label>
              {!wallet?.can_request_payout ? (
                <p className="trainer-education-muted">Недостаточно доступного баланса для минимальной выплаты.</p>
              ) : null}
              <div className="trainer-payout-actions">
                <button className="premium-primary-button" type="submit" disabled={!canSubmit || isSubmitting}>
                  {isSubmitting ? 'Создаём заявку' : 'Создать заявку'}
                </button>
                <Link className="premium-secondary-button" href="/trainer/dashboard/revenue">
                  Вернуться к финансам
                </Link>
              </div>
            </form>
          </article>

          <article className="trainer-payout-flow-card">
            <h3>Как проходит выплата</h3>
            <ol className="trainer-payout-timeline">
              <li>Вы создаёте заявку.</li>
              <li>Сумма временно резервируется.</li>
              <li>Финансовый администратор проверяет риски и реквизиты.</li>
              <li>Заявка проходит статусы: проверка → обработка → выплачено.</li>
              <li>Если заявку отклонят, сумма вернётся на доступный баланс.</li>
            </ol>
          </article>
        </div>

        <aside className="trainer-education-sidebar">
          <article className="trainer-payout-wallet-card">
            <h3>Баланс</h3>
            <KpiCard label="Доступно сейчас" value={formatMoney(wallet?.available_amount, currency)} />
            <KpiCard label="Резерв и блокировки" value={formatMoney(wallet?.locked_amount, currency)} />
          </article>

          <article className="trainer-payout-request-card">
            <div className="trainer-education-row">
              <h3>История заявок</h3>
              <button className="premium-secondary-button" type="button" onClick={load} disabled={isLoading}>
                Обновить
              </button>
            </div>
            <div className="trainer-payout-timeline">
              {(state.payouts?.results ?? []).map((payout) => (
                <article className="trainer-payout-timeline-card" key={payout.id}>
                  <div className="trainer-education-row">
                    <div>
                      <strong>{formatMoney(payout.amount, payout.currency)}</strong>
                      <p>{formatDateTime(payout.created_at)}</p>
                    </div>
                    <span className={badgeClass(payout.status)}>{mapPayoutStatusLabel(payout.status)}</span>
                  </div>
                  <span>{payout.destination_masked || 'Реквизиты не указаны'}</span>
                  <small className="trainer-education-muted">{statusHint(payout)}</small>
                </article>
              ))}
              {(state.payouts?.results ?? []).length === 0 ? (
                <div className="trainer-education-empty">
                  <strong>Заявок пока нет</strong>
                  <p>Заявок пока нет. Создайте первую выплату, когда баланс достигнет минимальной суммы.</p>
                </div>
              ) : null}
            </div>
          </article>
        </aside>
      </section>
    </section>
  );
}
