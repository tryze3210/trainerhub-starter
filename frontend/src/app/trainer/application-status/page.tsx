'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { ErrorCard, LoadingCard } from '@/components/async-state';
import { ProtectedPage } from '@/components/protected-page';
import { TrainerDashboardShell } from '@/modules/trainer-dashboard/components/trainer-dashboard-shell';
import { trainerStatusLabel } from '@/modules/trainer-cabinet/components/trainer-format';
import { trainerOnboardingApi, type TrainerOnboardingState } from '@/modules/trainer-onboarding/api';

function statusTone(status?: string): 'secondary' | 'warning' | 'success' | 'danger' {
  if (status === 'approved') return 'success';
  if (status === 'rejected') return 'danger';
  if (status === 'under_review' || status === 'changes_requested') return 'warning';
  return 'secondary';
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
      setError(err instanceof Error ? err.message : 'Не удалось загрузить статус заявки');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  return (
    <ProtectedPage
      title="Статус заявки тренера"
      description="Здесь отображается статус проверки и шаги, которые нужны для публикации продуктов."
    >
      <TrainerDashboardShell
        title="Статус заявки тренера"
        description="Здесь отображается статус проверки и шаги, которые нужны для публикации продуктов."
      >
        {loading ? <LoadingCard text="Загружаем статус…" /> : null}
        {error ? <ErrorCard text={`Статус недоступен: ${error}`} /> : null}
        {state ? (
          <div className="stack" style={{ gap: 24 }}>
            <section className="grid-3">
              <div className="card stat-card">
                <span className="stat-label">Проверка</span>
                <strong>{trainerStatusLabel(state.application.status)}</strong>
                <small>{state.application.reviewed_at || state.application.submitted_at || 'Не отправлено'}</small>
              </div>
              <div className="card stat-card">
                <span className="stat-label">Доступ к кабинету</span>
                <strong>{state.dashboard_unlocked ? 'Открыт' : 'Закрыт'}</strong>
                <small>{state.summary.next_step_title}</small>
              </div>
              <div className="card stat-card">
                <span className="stat-label">Прогресс</span>
                <strong>{state.summary.completion_percent}%</strong>
                <small>{state.summary.completed_steps}/{state.summary.total_steps} шагов</small>
              </div>
            </section>

            <section className="card stack" style={{ gap: 14 }}>
              <div className="row">
                <div>
                  <span className={`badge ${statusTone(state.application.status)}`}>{trainerStatusLabel(state.application.status)}</span>
                  <h2 className="title-md" style={{ marginTop: 8 }}>Результат проверки</h2>
                </div>
                <Link className="button secondary" href="/trainer/onboarding">Редактировать заявку</Link>
              </div>
              {state.application.reviewer_note ? <div className="warning-banner">{state.application.reviewer_note}</div> : null}
              {state.dashboard_unlocked ? (
                <Link className="button" href="/trainer/dashboard/products">Перейти к продуктам</Link>
              ) : (
                <p className="muted">Кабинет тренера откроется после проверки и синхронизации профиля.</p>
              )}
            </section>

            <section className="card stack" style={{ gap: 14 }}>
              <h2 className="title-md">Шаги готовности</h2>
              {state.steps.map((step) => (
                <div key={step.code} className="row">
                  <div>
                    <strong>{step.title}</strong>
                    <p className="muted">{step.description}</p>
                  </div>
                  <span className={`badge ${step.is_completed ? 'success' : step.is_blocked ? 'warning' : 'secondary'}`}>
                    {step.is_completed ? 'Готово' : step.is_blocked ? 'Нужно исправить' : 'Открыто'}
                  </span>
                </div>
              ))}
            </section>
          </div>
        ) : null}
      </TrainerDashboardShell>
    </ProtectedPage>
  );
}
