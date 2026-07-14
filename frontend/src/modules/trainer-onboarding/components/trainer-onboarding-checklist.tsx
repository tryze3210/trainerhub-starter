'use client';

import Link from 'next/link';
import { memo, useCallback, useEffect, useMemo, useRef, useState, type FormEvent } from 'react';
import {
  trainerOnboardingApi,
  type TrainerApplicationPayload,
  type TrainerOnboardingState,
} from '@/modules/trainer-onboarding/api';

type FormState = {
  legal_name: string;
  brand_name: string;
  contact_phone: string;
  country: string;
  city: string;
  bio: string;
  specialties_text: string;
  links_text: string;
  experience_years: string;
};

const emptyForm: FormState = {
  legal_name: '',
  brand_name: '',
  contact_phone: '',
  country: '',
  city: '',
  bio: '',
  specialties_text: '',
  links_text: '',
  experience_years: '',
};

function normalizeDelimitedList(value: string): string[] {
  return value
    .split(/\n|,/g)
    .map((item) => item.trim())
    .filter(Boolean);
}

function formatMoney(value?: string | number | null, currency = 'RUB') {
  const amount = Number(value || 0);
  return new Intl.NumberFormat('ru-RU', {
    style: 'currency',
    currency,
    maximumFractionDigits: 0,
  }).format(Number.isFinite(amount) ? amount : 0);
}

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

function buildPayload(form: FormState): TrainerApplicationPayload {
  const years = Number(form.experience_years);
  return {
    legal_name: form.legal_name.trim(),
    brand_name: form.brand_name.trim(),
    contact_phone: form.contact_phone.trim(),
    country: form.country.trim(),
    city: form.city.trim(),
    bio: form.bio.trim(),
    specialties: normalizeDelimitedList(form.specialties_text),
    links: normalizeDelimitedList(form.links_text),
    experience_years: Number.isFinite(years) && years >= 0 ? years : 0,
  };
}

function formDataToState(formData: FormData): FormState {
  return {
    legal_name: String(formData.get('legal_name') || ''),
    brand_name: String(formData.get('brand_name') || ''),
    contact_phone: String(formData.get('contact_phone') || ''),
    country: String(formData.get('country') || ''),
    city: String(formData.get('city') || ''),
    bio: String(formData.get('bio') || ''),
    specialties_text: String(formData.get('specialties_text') || ''),
    links_text: String(formData.get('links_text') || ''),
    experience_years: String(formData.get('experience_years') || ''),
  };
}

function stateToForm(state: TrainerOnboardingState | null): FormState {
  const application = state?.application;
  if (!application) return emptyForm;
  return {
    legal_name: application.legal_name || '',
    brand_name: application.brand_name || '',
    contact_phone: application.contact_phone || '',
    country: application.country || '',
    city: application.city || '',
    bio: application.bio || '',
    specialties_text: (application.specialties || []).join(', '),
    links_text: (application.links || []).join('\n'),
    experience_years: application.experience_years != null ? String(application.experience_years) : '',
  };
}

type TrainerApplicationFormProps = {
  initialForm: FormState;
  canEdit: boolean;
  canSubmit: boolean;
  saving: boolean;
  onSave: (payload: TrainerApplicationPayload) => Promise<void>;
  onSubmitApplication: (payload: TrainerApplicationPayload) => Promise<void>;
};

const TrainerApplicationForm = memo(function TrainerApplicationForm({
  initialForm,
  canEdit,
  canSubmit,
  saving,
  onSave,
  onSubmitApplication,
}: TrainerApplicationFormProps) {
  const formRef = useRef<HTMLFormElement>(null);
  const [localError, setLocalError] = useState('');
  const canSubmitCurrentDraft = canEdit || canSubmit;

  const getPayload = useCallback(() => {
    const form = formRef.current;
    return buildPayload(form ? formDataToState(new FormData(form)) : initialForm);
  }, [initialForm]);

  const validateForSubmit = useCallback((payload: TrainerApplicationPayload) => {
    if (!(payload.brand_name || payload.legal_name)) return 'Укажите название бренда или юридическое имя.';
    if (!payload.bio) return 'Добавьте позиционирование и описание.';
    if (!payload.specialties?.length) return 'Укажите хотя бы одну специализацию.';
    return '';
  }, []);

  async function saveDraft(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLocalError('');
    await onSave(getPayload());
  }

  async function submitApplication() {
    const payload = getPayload();
    const validationError = validateForSubmit(payload);
    if (validationError) {
      setLocalError(validationError);
      return;
    }
    setLocalError('');
    await onSubmitApplication(payload);
  }

  return (
    <form className="trainer-onboarding-form" ref={formRef} onSubmit={saveDraft}>
      <div className="trainer-onboarding-form-grid">
        <label className="trainer-onboarding-field">
          <span>Название бренда</span>
          <input name="brand_name" defaultValue={initialForm.brand_name} />
        </label>
        <label className="trainer-onboarding-field">
          <span>Юридическое имя</span>
          <input name="legal_name" defaultValue={initialForm.legal_name} />
        </label>
      </div>

      <div className="trainer-onboarding-form-grid">
        <label className="trainer-onboarding-field">
          <span>Телефон</span>
          <input name="contact_phone" defaultValue={initialForm.contact_phone} />
        </label>
        <label className="trainer-onboarding-field">
          <span>Опыт в годах</span>
          <input name="experience_years" type="number" min={0} defaultValue={initialForm.experience_years} />
        </label>
      </div>

      <div className="trainer-onboarding-form-grid">
        <label className="trainer-onboarding-field">
          <span>Страна</span>
          <input name="country" defaultValue={initialForm.country} />
        </label>
        <label className="trainer-onboarding-field">
          <span>Город</span>
          <input name="city" defaultValue={initialForm.city} />
        </label>
      </div>

      <label className="trainer-onboarding-field">
        <span>Позиционирование и описание</span>
        <textarea name="bio" rows={5} defaultValue={initialForm.bio} />
      </label>

      <label className="trainer-onboarding-field">
        <span>Специализации</span>
        <input
          name="specialties_text"
          placeholder="силовые тренировки, мобильность, снижение веса"
          defaultValue={initialForm.specialties_text}
        />
      </label>

      <label className="trainer-onboarding-field">
        <span>Ссылки</span>
        <textarea name="links_text" rows={3} defaultValue={initialForm.links_text} />
      </label>

      {localError ? <div className="trainer-onboarding-alert">{localError}</div> : null}

      <div className="trainer-onboarding-actions">
        <button className="premium-secondary-button" type="submit" disabled={saving || !canEdit}>
          {saving ? 'Сохраняем…' : 'Сохранить черновик'}
        </button>
        <button
          className="premium-primary-button"
          type="button"
          onClick={() => void submitApplication()}
          disabled={saving || !canSubmitCurrentDraft}
        >
          {saving ? 'Отправляем…' : 'Отправить на проверку'}
        </button>
      </div>
    </form>
  );
});

export function TrainerOnboardingChecklist() {
  const [state, setState] = useState<TrainerOnboardingState | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  async function load() {
    try {
      setLoading(true);
      setError('');
      const payload = await trainerOnboardingApi.getStatus();
      setState(payload);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось загрузить профиль тренера');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  const initialForm = useMemo(() => stateToForm(state), [state]);

  const saveDraft = useCallback(async (payload: TrainerApplicationPayload) => {
    try {
      setSaving(true);
      setError('');
      setMessage('');
      await trainerOnboardingApi.saveApplication(payload);
      setMessage('Черновик заявки сохранён.');
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось сохранить заявку');
    } finally {
      setSaving(false);
    }
  }, []);

  const submitApplication = useCallback(async (payload: TrainerApplicationPayload) => {
    try {
      setSaving(true);
      setError('');
      setMessage('');
      await trainerOnboardingApi.submitApplication(payload);
      setMessage('Заявка отправлена на проверку.');
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось отправить заявку');
    } finally {
      setSaving(false);
    }
  }, []);

  if (loading) {
    return (
      <div className="trainer-onboarding-workbench">
        <section className="trainer-onboarding-form-card">
          <h3>Загружаем профиль тренера</h3>
          <p className="trainer-onboarding-muted">Подготавливаем заявку и шаги готовности.</p>
        </section>
      </div>
    );
  }

  if (error && !state) {
    return (
      <div className="trainer-onboarding-workbench">
        <section className="trainer-onboarding-alert">
          <h3>Профиль тренера недоступен</h3>
          <p>{error}</p>
          <button className="premium-secondary-button" type="button" onClick={() => void load()}>
            Повторить
          </button>
        </section>
      </div>
    );
  }

  const dashboardUnlocked = Boolean(state?.dashboard_unlocked);
  const applicationStatus = state?.application.status || 'draft';
  const nextStep = state?.summary.next_step_title || 'Заполнить заявку';
  const submittedAt = formatDateTime(state?.application.submitted_at);

  return (
    <div className="trainer-onboarding-workbench">
      <section className="trainer-onboarding-hero">
        <div>
          <span className="trainer-onboarding-eyebrow">Заявка и профиль</span>
          <h2>Профиль тренера</h2>
          <p>Заполните данные, чтобы пройти проверку и открыть продажи</p>
          <div className="trainer-onboarding-actions">
            <Link className="premium-secondary-button" href="/trainer/application-status">Смотреть статус проверки</Link>
            {dashboardUnlocked ? <Link className="premium-primary-button" href="/trainer/dashboard/products">Открыть продукты</Link> : null}
          </div>
        </div>
        <div className="trainer-onboarding-status-card">
          <span>Прогресс заполнения</span>
          <strong>{formatPercent(state?.summary.completion_percent)}</strong>
          <small>
            {mapTrainerApplicationStatusLabel(applicationStatus)} · {dashboardUnlocked ? 'Кабинет открыт' : 'Кабинет закрыт'} · {mapRoleLabel(state?.user?.role)}
          </small>
        </div>
      </section>

      <section className="trainer-onboarding-kpi-grid">
        <article className="trainer-onboarding-status-card">
          <span>Прогресс</span>
          <strong>{formatPercent(state?.summary.completion_percent)}</strong>
          <small>{state?.summary.completed_steps || 0}/{state?.summary.total_steps || 0} шагов</small>
        </article>
        <article className="trainer-onboarding-status-card">
          <span>Статус заявки</span>
          <strong>{mapTrainerApplicationStatusLabel(applicationStatus)}</strong>
          <small>{submittedAt}</small>
        </article>
        <article className="trainer-onboarding-status-card">
          <span>Кабинет</span>
          <strong>{dashboardUnlocked ? 'Открыт' : 'Закрыт'}</strong>
          <small>{dashboardUnlocked ? 'Можно публиковать продукты' : 'Ожидает одобрения'}</small>
        </article>
        <article className="trainer-onboarding-status-card">
          <span>Роль</span>
          <strong>{mapRoleLabel(state?.user?.role)}</strong>
          <small>Роль тренера выдаётся после одобрения заявки</small>
        </article>
      </section>

      {message ? <div className="trainer-onboarding-alert trainer-onboarding-alert-success">{message}</div> : null}
      {error ? <div className="trainer-onboarding-alert">{error}</div> : null}

      <section className="trainer-onboarding-layout">
        <main className="trainer-onboarding-main">
          <section className="trainer-onboarding-form-card">
            <div className="trainer-onboarding-panel-head">
              <div>
                <span className={`trainer-onboarding-status trainer-onboarding-status-${getBadgeTone(applicationStatus)}`}>
                  {mapTrainerApplicationStatusLabel(applicationStatus)}
                </span>
                <h3>Заявка тренера</h3>
                <p>После одобрения заявки система откроет кабинет тренера, синхронизирует публичный профиль и разрешит публикацию продуктов.</p>
              </div>
              <Link className="premium-secondary-button" href="/trainer/application-status">Смотреть статус проверки</Link>
            </div>

            {state?.application.reviewer_note ? (
              <div className="trainer-onboarding-alert">
                <strong>Комментарий модерации:</strong> {state.application.reviewer_note}
              </div>
            ) : null}

            <TrainerApplicationForm
              key={state?.application.updated_at || state?.application.id || 'trainer-application-form'}
              initialForm={initialForm}
              canEdit={Boolean(state?.can_edit_application)}
              canSubmit={Boolean(state?.can_submit_application)}
              saving={saving}
              onSave={saveDraft}
              onSubmitApplication={submitApplication}
            />
          </section>
        </main>

        <aside className="trainer-onboarding-sidebar">
          <section className="trainer-onboarding-form-card">
            <h3>Шаги готовности</h3>
            <p className="trainer-onboarding-muted">{nextStep}</p>
            <div className="trainer-onboarding-step-list">
              {(state?.steps || []).map((step) => {
                const stepStatus = step.is_completed ? 'completed' : step.is_blocked ? 'blocked' : 'open';
                return (
                  <article className="trainer-onboarding-step-card" key={step.code}>
                    <div>
                      <strong>{step.title}</strong>
                      <p>{step.description}</p>
                    </div>
                    <span className={`trainer-onboarding-status trainer-onboarding-status-${getBadgeTone(stepStatus)}`}>
                      {mapStepStatusLabel(stepStatus)}
                    </span>
                    {step.action_href ? <Link className="premium-secondary-button" href={step.action_href}>Открыть</Link> : null}
                  </article>
                );
              })}
              {!state?.steps.length ? <div className="trainer-onboarding-empty">Шаги готовности пока не сформированы.</div> : null}
            </div>
          </section>

          <section className="trainer-onboarding-form-card">
            <h3>Сводка профиля</h3>
            <article className="trainer-onboarding-step-card">
              <strong>{state?.profile?.display_name || state?.application.brand_name || 'Публичное имя не указано'}</strong>
              <p>{state?.profile?.headline || state?.application.bio || 'Описание появится после заполнения заявки.'}</p>
            </article>
            <article className="trainer-onboarding-step-card">
              <strong>{shortId(state?.application.id)}</strong>
              <p>{mapReadinessStatusLabel(state?.summary.status)} · {mapModerationStatusLabel(applicationStatus)}</p>
            </article>
          </section>
        </aside>
      </section>
    </div>
  );
}
