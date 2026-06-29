'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { ProtectedPage } from '@/components/protected-page';
import { TrainerDashboardShell } from '@/modules/trainer-dashboard/components/trainer-dashboard-shell';
import { trainerOnboardingApi, type TrainerOnboardingState } from '@/modules/trainer-onboarding/api';

function formatDateTime(value?: string | null) {
  if (!value) return 'Дата не указана';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat('ru-RU', {
    day: '2-digit',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date);
}

function formatPercent(value?: string | number | null) {
  const amount = Number(value || 0);
  return `${Number.isFinite(amount) ? Math.round(amount) : 0}%`;
}

function mapTrainerApplicationStatusLabel(status?: string | null) {
  const labels: Record<string, string> = {
    draft: 'Черновик',
    submitted: 'Отправлена',
    under_review: 'На проверке',
    approved: 'Одобрена',
    changes_requested: 'Нужны правки',
    rejected: 'Отклонена',
  };
  return labels[status || ''] || 'Черновик';
}

function mapReadinessStatusLabel(status?: string | null) {
  const labels: Record<string, string> = {
    ready: 'Готово',
    done: 'Готово',
    approved: 'Одобрено',
    paid: 'Оплачено',
    healthy: 'Норма',
    blocked: 'Заблокировано',
    blocker: 'Блокер',
    critical: 'Критично',
    rejected: 'Отклонено',
    warning: 'Требует внимания',
    pending: 'Ожидает',
  };
  return labels[status || ''] || 'Не проверено';
}

function mapStepStatusLabel(status?: string | null) {
  const labels: Record<string, string> = {
    completed: 'Готово',
    blocked: 'Нужно исправить',
    open: 'Открыто',
  };
  return labels[status || ''] || 'Открыто';
}

function mapRoleLabel(role?: string | null) {
  const labels: Record<string, string> = {
    customer: 'Клиент',
    trainer: 'Тренер',
    admin: 'Администратор',
  };
  return labels[role || ''] || 'Пользователь';
}

function mapProductTypeLabel(type?: string | null) {
  const labels: Record<string, string> = {
    video: 'Видео',
    course: 'Курс',
    program: 'Программа',
    product: 'Продукт',
    bundle: 'Набор',
  };
  return labels[type || ''] || 'Материал';
}

function mapPayoutStatusLabel(status?: string | null) {
  const labels: Record<string, string> = {
    pending: 'На проверке',
    approved: 'Одобрено',
    processing: 'В обработке',
    paid: 'Выплачено',
    rejected: 'Отклонено',
    cancelled: 'Отменено',
    failed: 'Ошибка выплаты',
  };
  return labels[status || ''] || 'Не проверено';
}

function mapModerationStatusLabel(status?: string | null) {
  const labels: Record<string, string> = {
    open: 'Открыто',
    pending: 'Ожидает',
    under_review: 'На проверке',
    approved: 'Одобрено',
    rejected: 'Отклонено',
    blocked: 'Заблокировано',
    resolved: 'Решено',
    closed: 'Закрыто',
  };
  return labels[status || ''] || 'Не проверено';
}

function getBadgeTone(status?: string | null) {
  if (['ready', 'done', 'approved', 'paid', 'healthy', 'completed', 'resolved', 'closed'].includes(status || '')) return 'success';
  if (['blocked', 'blocker', 'critical', 'rejected', 'failed'].includes(status || '')) return 'danger';
  if (['warning', 'pending', 'under_review', 'changes_requested', 'processing', 'submitted', 'open'].includes(status || '')) return 'warning';
  return 'neutral';
}

function shortId(value?: string | null) {
  if (!value) return 'без номера';
  return value.length > 10 ? `${value.slice(0, 6)}…${value.slice(-4)}` : value;
}

export default function TrainerApplicationStatusPage() {
  const [state, setState] = useState<TrainerOnboardingState | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  async function load() {
    try {
      setLoading(true);
      setError('');
      setState(await trainerOnboardingApi.getApplicationStatus());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось загрузить статус проверки');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  const applicationStatus = state?.application.status || 'draft';
  const dashboardUnlocked = Boolean(state?.dashboard_unlocked);
  const nextStep = state?.summary.next_step_title || 'Заполнить заявку';

  return (
    <ProtectedPage
      title="Статус проверки"
      description="Модерация заявки, доступ к кабинету и следующие шаги"
    >
      <TrainerDashboardShell
        title="Статус проверки"
        description="Модерация заявки, доступ к кабинету и следующие шаги"
      >
        <div className="trainer-status-workbench">
          <section className="trainer-status-hero">
            <div>
              <span className="trainer-status-eyebrow">Проверка тренера</span>
              <h2>Статус проверки</h2>
              <p>Модерация заявки, доступ к кабинету и следующие шаги</p>
              <div className="trainer-status-actions">
                <Link className="premium-secondary-button" href="/trainer/onboarding">Редактировать заявку</Link>
                {dashboardUnlocked ? <Link className="premium-primary-button" href="/trainer/dashboard/products">Перейти к продуктам</Link> : null}
              </div>
            </div>
            <div className="trainer-status-result-card">
              <span>Текущий статус заявки</span>
              <strong>{mapTrainerApplicationStatusLabel(applicationStatus)}</strong>
              <small>{dashboardUnlocked ? 'Кабинет открыт' : 'Кабинет тренера откроется после проверки и синхронизации профиля.'}</small>
            </div>
          </section>

          {loading ? (
            <section className="trainer-status-panel">
              <h3>Загружаем статус проверки</h3>
              <p className="trainer-status-muted">Получаем заявку, доступ к кабинету и шаги готовности.</p>
            </section>
          ) : null}

          {error ? (
            <section className="trainer-status-panel trainer-status-alert">
              <h3>Статус недоступен</h3>
              <p>{error}</p>
              <button className="premium-secondary-button" type="button" onClick={() => void load()}>
                Повторить
              </button>
            </section>
          ) : null}

          {state ? (
            <>
              <section className="trainer-status-kpi-grid">
                <article className="trainer-status-result-card">
                  <span>Проверка</span>
                  <strong>{mapTrainerApplicationStatusLabel(applicationStatus)}</strong>
                  <small>{formatDateTime(state.application.reviewed_at || state.application.submitted_at)}</small>
                </article>
                <article className="trainer-status-result-card">
                  <span>Доступ к кабинету</span>
                  <strong>{dashboardUnlocked ? 'Открыт' : 'Закрыт'}</strong>
                  <small>{mapRoleLabel(state.user.role)}</small>
                </article>
                <article className="trainer-status-result-card">
                  <span>Прогресс</span>
                  <strong>{formatPercent(state.summary.completion_percent)}</strong>
                  <small>{state.summary.completed_steps}/{state.summary.total_steps} шагов</small>
                </article>
                <article className="trainer-status-result-card">
                  <span>Следующий шаг</span>
                  <strong>{nextStep}</strong>
                  <small>{mapReadinessStatusLabel(state.summary.status)}</small>
                </article>
              </section>

              <section className="trainer-status-layout">
                <main className="trainer-status-panel">
                  <div className="trainer-status-panel-head">
                    <div>
                      <span className={`trainer-status-pill trainer-status-pill-${getBadgeTone(applicationStatus)}`}>
                        {mapTrainerApplicationStatusLabel(applicationStatus)}
                      </span>
                      <h3>Результат проверки</h3>
                      <p>{dashboardUnlocked ? 'Профиль синхронизирован, кабинет тренера открыт.' : 'Кабинет тренера откроется после проверки и синхронизации профиля.'}</p>
                    </div>
                    <Link className="premium-secondary-button" href="/trainer/onboarding">Редактировать заявку</Link>
                  </div>

                  {state.application.reviewer_note ? (
                    <div className="trainer-status-alert">
                      <strong>Комментарий модерации:</strong> {state.application.reviewer_note}
                    </div>
                  ) : null}

                  <div className="trainer-status-result-grid">
                    <article className="trainer-status-result-card">
                      <span>Номер заявки</span>
                      <strong>{shortId(state.application.id)}</strong>
                      <small>{mapModerationStatusLabel(applicationStatus)}</small>
                    </article>
                    <article className="trainer-status-result-card">
                      <span>Тип доступа</span>
                      <strong>{mapProductTypeLabel('product')}</strong>
                      <small>{dashboardUnlocked ? 'Можно готовить продукты' : 'Будет доступен после проверки'}</small>
                    </article>
                  </div>
                </main>

                <aside className="trainer-status-panel">
                  <h3>Шаги готовности</h3>
                  <div className="trainer-status-timeline">
                    {state.steps.map((step) => {
                      const stepStatus = step.is_completed ? 'completed' : step.is_blocked ? 'blocked' : 'open';
                      return (
                        <article className="trainer-status-step-card" key={step.code}>
                          <div>
                            <strong>{step.title}</strong>
                            <p>{step.description}</p>
                          </div>
                          <span className={`trainer-status-pill trainer-status-pill-${getBadgeTone(stepStatus)}`}>
                            {mapStepStatusLabel(stepStatus)}
                          </span>
                          {step.action_href ? <Link className="premium-secondary-button" href={step.action_href}>Открыть</Link> : null}
                        </article>
                      );
                    })}
                    {!state.steps.length ? <div className="trainer-status-empty">Шаги готовности пока не сформированы.</div> : null}
                  </div>
                </aside>
              </section>
            </>
          ) : null}
        </div>
      </TrainerDashboardShell>
    </ProtectedPage>
  );
}
