'use client';

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import { ErrorCard, LoadingCard } from '@/components/async-state';
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

function statusTone(status?: string): 'secondary' | 'warning' | 'success' | 'danger' {
  if (status === 'approved') return 'success';
  if (status === 'rejected') return 'danger';
  if (status === 'under_review' || status === 'submitted' || status === 'changes_requested') return 'warning';
  return 'secondary';
}

function statusLabel(status?: string) {
  const labels: Record<string, string> = {
    draft: 'Draft',
    submitted: 'Submitted',
    under_review: 'Under review',
    approved: 'Approved',
    changes_requested: 'Changes requested',
    rejected: 'Rejected',
  };
  return labels[status || ''] || 'Draft';
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

export function TrainerOnboardingChecklist() {
  const [state, setState] = useState<TrainerOnboardingState | null>(null);
  const [form, setForm] = useState<FormState>(emptyForm);
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
      setForm(stateToForm(payload));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось загрузить onboarding');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  const applicationReady = useMemo(() => {
    const payload = buildPayload(form);
    return Boolean((payload.brand_name || payload.legal_name) && payload.bio && payload.specialties?.length);
  }, [form]);

  async function saveDraft(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    try {
      setSaving(true);
      setError('');
      setMessage('');
      await trainerOnboardingApi.saveApplication(buildPayload(form));
      setMessage('Черновик заявки сохранён.');
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось сохранить заявку');
    } finally {
      setSaving(false);
    }
  }

  async function submitApplication() {
    try {
      setSaving(true);
      setError('');
      setMessage('');
      await trainerOnboardingApi.submitApplication(buildPayload(form));
      setMessage('Заявка отправлена на модерацию.');
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось отправить заявку');
    } finally {
      setSaving(false);
    }
  }

  if (loading) return <LoadingCard text="Загружаем trainer onboarding…" />;
  if (error && !state) return <ErrorCard text={`Onboarding недоступен: ${error}`} />;

  const tone = statusTone(state?.application.status);
  const dashboardUnlocked = Boolean(state?.dashboard_unlocked);

  return (
    <div className="stack" style={{ gap: 24 }}>
      <section className="grid-4">
        <div className="card stat-card">
          <span className="stat-label">Progress</span>
          <strong>{state?.summary.completion_percent || 0}%</strong>
          <small>{state?.summary.completed_steps || 0}/{state?.summary.total_steps || 0} steps</small>
        </div>
        <div className="card stat-card">
          <span className="stat-label">Application</span>
          <strong>{statusLabel(state?.application.status)}</strong>
          <small>{state?.summary.next_step_title}</small>
        </div>
        <div className="card stat-card">
          <span className="stat-label">Dashboard</span>
          <strong>{dashboardUnlocked ? 'Unlocked' : 'Locked'}</strong>
          <small>{dashboardUnlocked ? 'Можно публиковать продукты' : 'Ждёт approve'}</small>
        </div>
        <div className="card stat-card">
          <span className="stat-label">Role</span>
          <strong>{state?.user.role || 'customer'}</strong>
          <small>Trainer role выдаётся после approval</small>
        </div>
      </section>

      {message ? <div className="success-banner">{message}</div> : null}
      {error ? <div className="error-banner">{error}</div> : null}

      <section className="card stack" style={{ gap: 18 }}>
        <div className="row">
          <div>
            <span className={`badge ${tone}`}>{statusLabel(state?.application.status)}</span>
            <h2 className="title-md" style={{ marginTop: 10 }}>Trainer application</h2>
            <p className="muted">
              Обычный пользователь может заполнить и отправить заявку. После approval система выдаёт trainer role,
              создаёт/sync profile и разблокирует dashboard.
            </p>
          </div>
          <Link className="button secondary" href="/trainer/application-status">
            Смотреть статус
          </Link>
        </div>

        {state?.application.reviewer_note ? (
          <div className="warning-banner">
            <strong>Комментарий модерации:</strong> {state.application.reviewer_note}
          </div>
        ) : null}

        <form className="form" onSubmit={saveDraft}>
          <div className="grid-2">
            <label className="form-group">
              <span className="label">Brand name</span>
              <input className="input" value={form.brand_name} onChange={(event) => setForm((prev) => ({ ...prev, brand_name: event.target.value }))} />
            </label>
            <label className="form-group">
              <span className="label">Legal name</span>
              <input className="input" value={form.legal_name} onChange={(event) => setForm((prev) => ({ ...prev, legal_name: event.target.value }))} />
            </label>
          </div>

          <div className="grid-2">
            <label className="form-group">
              <span className="label">Phone</span>
              <input className="input" value={form.contact_phone} onChange={(event) => setForm((prev) => ({ ...prev, contact_phone: event.target.value }))} />
            </label>
            <label className="form-group">
              <span className="label">Experience years</span>
              <input className="input" type="number" min={0} value={form.experience_years} onChange={(event) => setForm((prev) => ({ ...prev, experience_years: event.target.value }))} />
            </label>
          </div>

          <div className="grid-2">
            <label className="form-group">
              <span className="label">Country</span>
              <input className="input" value={form.country} onChange={(event) => setForm((prev) => ({ ...prev, country: event.target.value }))} />
            </label>
            <label className="form-group">
              <span className="label">City</span>
              <input className="input" value={form.city} onChange={(event) => setForm((prev) => ({ ...prev, city: event.target.value }))} />
            </label>
          </div>

          <label className="form-group">
            <span className="label">Positioning / bio</span>
            <textarea className="textarea" rows={5} value={form.bio} onChange={(event) => setForm((prev) => ({ ...prev, bio: event.target.value }))} />
          </label>

          <label className="form-group">
            <span className="label">Specialties</span>
            <input className="input" placeholder="strength, mobility, fat loss" value={form.specialties_text} onChange={(event) => setForm((prev) => ({ ...prev, specialties_text: event.target.value }))} />
          </label>

          <label className="form-group">
            <span className="label">Links</span>
            <textarea className="textarea" rows={3} value={form.links_text} onChange={(event) => setForm((prev) => ({ ...prev, links_text: event.target.value }))} />
          </label>

          <div className="inline">
            <button className="button secondary" type="submit" disabled={saving || !state?.can_edit_application}>
              {saving ? 'Сохраняем…' : 'Сохранить draft'}
            </button>
            <button className="button" type="button" onClick={() => void submitApplication()} disabled={saving || !applicationReady || !state?.can_submit_application}>
              {saving ? 'Отправляем…' : 'Отправить на модерацию'}
            </button>
          </div>
        </form>
      </section>

      <section className="card stack" style={{ gap: 14 }}>
        <h2 className="title-md">Production readiness steps</h2>
        {(state?.steps || []).map((step) => (
          <div key={step.code} className="row" style={{ alignItems: 'flex-start' }}>
            <div>
              <strong>{step.title}</strong>
              <p className="muted">{step.description}</p>
            </div>
            <span className={`badge ${step.is_completed ? 'success' : step.is_blocked ? 'warning' : 'secondary'}`}>
              {step.is_completed ? 'Completed' : step.is_blocked ? 'Blocked' : 'Open'}
            </span>
          </div>
        ))}
      </section>
    </div>
  );
}
