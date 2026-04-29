'use client';

import { useEffect, useMemo, useState } from 'react';
import { useAuthSession } from '@/components/auth-provider';
import { ErrorCard, LoadingCard } from '@/components/async-state';
import { onboardingApi } from '@/modules/trainer-onboarding/api';
import { trainersApi } from '@/modules/trainers/api';
import type {
  OnboardingStatus,
  TrainerApplication,
  TrainerApplicationPayload,
  TrainerProfile,
} from '@/types/api';

type ProfileFormState = {
  display_name: string;
  slug: string;
  headline: string;
  bio: string;
  is_public: boolean;
};

type ApplicationFormState = {
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

const emptyProfileForm: ProfileFormState = {
  display_name: '',
  slug: '',
  headline: '',
  bio: '',
  is_public: true,
};

const emptyApplicationForm: ApplicationFormState = {
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

function formatApplicationStatus(status?: string | null): {
  label: string;
  tone: 'secondary' | 'warning' | 'success' | 'danger';
  description: string;
} {
  switch (status) {
    case 'approved':
      return {
        label: 'Approved',
        tone: 'success',
        description: 'Заявка одобрена. Можно двигаться к публикации и продажам.',
      };
    case 'under_review':
    case 'submitted':
      return {
        label: 'Under review',
        tone: 'warning',
        description: 'Заявка уже отправлена. Сейчас важнее держать профиль и материалы в порядке.',
      };
    case 'changes_requested':
      return {
        label: 'Changes requested',
        tone: 'warning',
        description: 'Модерация вернула заявку с правками. Обнови данные и отправь повторно.',
      };
    case 'rejected':
      return {
        label: 'Rejected',
        tone: 'danger',
        description: 'Заявка отклонена. Исправь позиционирование и подай её заново.',
      };
    default:
      return {
        label: 'Draft',
        tone: 'secondary',
        description: 'Заявка ещё не отправлена. Сначала сохрани черновик и проверь обязательные поля.',
      };
  }
}

export function TrainerOnboardingChecklist() {
  const { user } = useAuthSession();
  const [status, setStatus] = useState<OnboardingStatus | null>(null);
  const [profile, setProfile] = useState<TrainerProfile | null>(null);
  const [application, setApplication] = useState<TrainerApplication | null>(null);
  const [profileForm, setProfileForm] = useState<ProfileFormState>(emptyProfileForm);
  const [applicationForm, setApplicationForm] = useState<ApplicationFormState>(emptyApplicationForm);
  const [loading, setLoading] = useState(true);
  const [savingProfile, setSavingProfile] = useState(false);
  const [savingApplication, setSavingApplication] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  async function load() {
    try {
      setLoading(true);
      setError('');
      const [statusPayload, profileResult, applicationResult] = await Promise.all([
        onboardingApi.status(),
        trainersApi.getMyProfile().catch(() => null),
        trainersApi.getMyApplication().catch(() => null),
      ]);
      setStatus(statusPayload);
      setProfile(profileResult);
      setApplication(applicationResult);
      setProfileForm({
        display_name: profileResult?.display_name || '',
        slug: profileResult?.slug || '',
        headline: profileResult?.headline || '',
        bio: profileResult?.bio || '',
        is_public: profileResult?.is_public ?? true,
      });
      setApplicationForm({
        legal_name: applicationResult?.legal_name || '',
        brand_name: applicationResult?.brand_name || '',
        contact_phone: applicationResult?.contact_phone || '',
        country: applicationResult?.country || '',
        city: applicationResult?.city || '',
        bio: applicationResult?.bio || '',
        specialties_text: (applicationResult?.specialties || []).join(', '),
        links_text: (applicationResult?.links || []).join('\n'),
        experience_years: applicationResult?.experience_years != null ? String(applicationResult.experience_years) : '',
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось загрузить onboarding');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  const canWorkAsTrainer = user?.active_role === 'trainer' || Boolean(user?.available_roles?.includes('trainer'));
  const completion = useMemo(() => `${status?.summary.completion_percent || 0}%`, [status]);
  const applicationStatus = formatApplicationStatus(application?.status || status?.trainer_application_status);
  const applicationReady = Boolean(
    (applicationForm.brand_name || applicationForm.legal_name).trim() &&
      applicationForm.bio.trim() &&
      normalizeDelimitedList(applicationForm.specialties_text).length
  );
  const profileReady = Boolean(profile?.display_name && profile?.slug);

  function buildApplicationPayload(): TrainerApplicationPayload {
    const experienceYears = Number(applicationForm.experience_years);
    return {
      legal_name: applicationForm.legal_name.trim(),
      brand_name: applicationForm.brand_name.trim(),
      contact_phone: applicationForm.contact_phone.trim(),
      country: applicationForm.country.trim(),
      city: applicationForm.city.trim(),
      bio: applicationForm.bio.trim(),
      specialties: normalizeDelimitedList(applicationForm.specialties_text),
      links: normalizeDelimitedList(applicationForm.links_text),
      experience_years: Number.isFinite(experienceYears) && experienceYears > 0 ? experienceYears : undefined,
    };
  }

  async function saveProfile(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    try {
      setSavingProfile(true);
      setError('');
      setMessage('');

      const payload = {
        display_name: profileForm.display_name,
        slug: profileForm.slug,
        headline: profileForm.headline,
        bio: profileForm.bio,
        is_public: profileForm.is_public,
      };

      const nextProfile = profile
        ? await trainersApi.updateMyProfile(payload)
        : await trainersApi.createMyProfile(payload);

      setProfile(nextProfile);
      await onboardingApi.completeStep('trainer_profile', {
        source: 'trainer-onboarding-profile',
      });
      setMessage('Профиль тренера сохранён.');
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось сохранить профиль');
    } finally {
      setSavingProfile(false);
    }
  }

  async function saveApplicationDraft(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    try {
      setSavingApplication(true);
      setError('');
      setMessage('');
      const nextApplication = await trainersApi.updateMyApplication(buildApplicationPayload());
      setApplication(nextApplication);
      setMessage('Черновик trainer application сохранён.');
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось сохранить заявку');
    } finally {
      setSavingApplication(false);
    }
  }

  async function submitApplication() {
    try {
      setSavingApplication(true);
      setError('');
      setMessage('');
      const nextApplication = await trainersApi.submitMyApplication(buildApplicationPayload());
      setApplication(nextApplication);
      setMessage('Заявка отправлена на модерацию.');
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось отправить заявку');
    } finally {
      setSavingApplication(false);
    }
  }

  if (!canWorkAsTrainer) {
    return (
      <div className="card warning">
        Этот раздел предназначен для роли trainer. Войди в trainer-аккаунт или зарегистрируйся с ролью тренера, чтобы отправить заявку на модерацию.
      </div>
    );
  }

  if (loading) {
    return <LoadingCard text="Загружаем onboarding тренера…" />;
  }

  if (error && !status) {
    return <ErrorCard text={error} />;
  }

  return (
    <div className="stack" style={{ gap: 24 }}>
      <div className="grid-4 trainer-metrics-grid">
        <div className="card trainer-metric-card">
          <span className="muted">Onboarding progress</span>
          <strong>{completion}</strong>
          <small>{status?.summary.completed_steps || 0}/{status?.summary.total_steps || 0} шагов закрыто</small>
        </div>
        <div className="card trainer-metric-card">
          <span className="muted">Application status</span>
          <strong>{applicationStatus.label}</strong>
          <small>{applicationStatus.description}</small>
        </div>
        <div className="card trainer-metric-card">
          <span className="muted">Profile readiness</span>
          <strong>{profileReady ? 'Ready' : 'In progress'}</strong>
          <small>{profileReady ? 'Публичный профиль уже можно использовать в витрине.' : 'Нужны display name и slug.'}</small>
        </div>
        <div className="card trainer-metric-card">
          <span className="muted">Next action</span>
          <strong>{status?.summary.next_step || 'Review queue'}</strong>
          <small>{applicationStatus.tone === 'success' ? 'Двигайся к контенту и первой публикации.' : 'Закрой ближайший блок перед публикацией.'}</small>
        </div>
      </div>

      {message ? <div className="card success">{message}</div> : null}
      {error ? <div className="card error">{error}</div> : null}

      <div className={`card trainer-status-banner trainer-status-banner--${applicationStatus.tone}`}>
        <div className="stack" style={{ gap: 8 }}>
          <div className="row">
            <div>
              <h2 className="title-md" style={{ marginBottom: 6 }}>Trainer application</h2>
              <p className="muted">Здесь живёт реальный статус модерации trainer-аккаунта, а не просто локальный чеклист.</p>
            </div>
            <span className={`badge ${applicationStatus.tone}`}>{applicationStatus.label}</span>
          </div>
          <p>{applicationStatus.description}</p>
          {application?.reviewer_note ? (
            <div className="trainer-note-box">
              <strong>Комментарий модерации</strong>
              <p>{application.reviewer_note}</p>
            </div>
          ) : null}
        </div>
      </div>

      <div className="grid-2 trainer-section-grid">
        <section className="card trainer-panel">
          <div className="row trainer-panel__header">
            <div>
              <h2 className="title-md" style={{ marginBottom: 6 }}>1. Публичный профиль тренера</h2>
              <p className="muted">Это storefront identity: имя, slug, headline и bio для каталога тренеров.</p>
            </div>
            <span className={`badge ${profileReady ? 'success' : 'warning'}`}>{profileReady ? 'Profile ready' : 'Profile required'}</span>
          </div>

          <form className="form" onSubmit={saveProfile}>
            <div className="grid-2">
              <div className="form-group">
                <label className="label" htmlFor="display_name">Display name</label>
                <input
                  id="display_name"
                  className="input"
                  value={profileForm.display_name}
                  onChange={(event) => setProfileForm((prev) => ({ ...prev, display_name: event.target.value }))}
                  required
                />
              </div>
              <div className="form-group">
                <label className="label" htmlFor="slug">Slug</label>
                <input
                  id="slug"
                  className="input"
                  value={profileForm.slug}
                  onChange={(event) => setProfileForm((prev) => ({ ...prev, slug: event.target.value }))}
                  required
                />
              </div>
            </div>

            <div className="form-group">
              <label className="label" htmlFor="headline">Headline</label>
              <input
                id="headline"
                className="input"
                value={profileForm.headline}
                onChange={(event) => setProfileForm((prev) => ({ ...prev, headline: event.target.value }))}
                placeholder="Например: strength coach / mobility trainer / postpartum recovery"
              />
            </div>

            <div className="form-group">
              <label className="label" htmlFor="profile_bio">Bio</label>
              <textarea
                id="profile_bio"
                className="textarea"
                value={profileForm.bio}
                onChange={(event) => setProfileForm((prev) => ({ ...prev, bio: event.target.value }))}
                rows={5}
                placeholder="Коротко опиши специализацию, формат тренировок и для кого твой продукт."
              />
            </div>

            <label className="checkbox-row">
              <input
                type="checkbox"
                checked={profileForm.is_public}
                onChange={(event) => setProfileForm((prev) => ({ ...prev, is_public: event.target.checked }))}
              />
              Сделать профиль публичным после прохождения модерации
            </label>

            <div className="inline">
              <button className="button" type="submit" disabled={savingProfile}>
                {savingProfile ? 'Сохраняем…' : profile ? 'Обновить профиль' : 'Создать профиль'}
              </button>
            </div>
          </form>
        </section>

        <section className="card trainer-panel">
          <div className="row trainer-panel__header">
            <div>
              <h2 className="title-md" style={{ marginBottom: 6 }}>2. Заявка на модерацию</h2>
              <p className="muted">Этот блок определяет, можно ли выдавать тебе trainer storefront и контентный publish flow.</p>
            </div>
            <span className={`badge ${applicationStatus.tone}`}>{applicationStatus.label}</span>
          </div>

          <form className="form" onSubmit={saveApplicationDraft}>
            <div className="grid-2">
              <div className="form-group">
                <label className="label" htmlFor="brand_name">Brand name</label>
                <input
                  id="brand_name"
                  className="input"
                  value={applicationForm.brand_name}
                  onChange={(event) => setApplicationForm((prev) => ({ ...prev, brand_name: event.target.value }))}
                  placeholder="Например: Coach Vlad"
                />
              </div>
              <div className="form-group">
                <label className="label" htmlFor="legal_name">Legal name</label>
                <input
                  id="legal_name"
                  className="input"
                  value={applicationForm.legal_name}
                  onChange={(event) => setApplicationForm((prev) => ({ ...prev, legal_name: event.target.value }))}
                  placeholder="ИП / физлицо / студия"
                />
              </div>
            </div>

            <div className="grid-2">
              <div className="form-group">
                <label className="label" htmlFor="contact_phone">Contact phone</label>
                <input
                  id="contact_phone"
                  className="input"
                  value={applicationForm.contact_phone}
                  onChange={(event) => setApplicationForm((prev) => ({ ...prev, contact_phone: event.target.value }))}
                  placeholder="+7 ..."
                />
              </div>
              <div className="form-group">
                <label className="label" htmlFor="experience_years">Experience years</label>
                <input
                  id="experience_years"
                  className="input"
                  type="number"
                  min={0}
                  value={applicationForm.experience_years}
                  onChange={(event) => setApplicationForm((prev) => ({ ...prev, experience_years: event.target.value }))}
                  placeholder="5"
                />
              </div>
            </div>

            <div className="grid-2">
              <div className="form-group">
                <label className="label" htmlFor="country">Country</label>
                <input
                  id="country"
                  className="input"
                  value={applicationForm.country}
                  onChange={(event) => setApplicationForm((prev) => ({ ...prev, country: event.target.value }))}
                />
              </div>
              <div className="form-group">
                <label className="label" htmlFor="city">City</label>
                <input
                  id="city"
                  className="input"
                  value={applicationForm.city}
                  onChange={(event) => setApplicationForm((prev) => ({ ...prev, city: event.target.value }))}
                />
              </div>
            </div>

            <div className="form-group">
              <label className="label" htmlFor="application_bio">Positioning / bio</label>
              <textarea
                id="application_bio"
                className="textarea"
                value={applicationForm.bio}
                onChange={(event) => setApplicationForm((prev) => ({ ...prev, bio: event.target.value }))}
                rows={5}
                placeholder="Опиши, кого ты тренируешь, в каком формате работаешь и чем отличаешься от других."
              />
            </div>

            <div className="form-group">
              <label className="label" htmlFor="specialties">Specialties</label>
              <input
                id="specialties"
                className="input"
                value={applicationForm.specialties_text}
                onChange={(event) => setApplicationForm((prev) => ({ ...prev, specialties_text: event.target.value }))}
                placeholder="strength, mobility, fat loss"
              />
              <small>Хотя бы одна специализация обязательна для отправки заявки.</small>
            </div>

            <div className="form-group">
              <label className="label" htmlFor="links">Links</label>
              <textarea
                id="links"
                className="textarea"
                value={applicationForm.links_text}
                onChange={(event) => setApplicationForm((prev) => ({ ...prev, links_text: event.target.value }))}
                rows={3}
                placeholder="Одна ссылка на строку: сайт, соцсети, портфолио"
              />
            </div>

            <div className="trainer-helper-list">
              <div className={`trainer-helper-list__item${applicationReady ? ' is-complete' : ''}`}>
                <strong>Brand or legal name</strong>
                <span>{(applicationForm.brand_name || applicationForm.legal_name).trim() ? 'OK' : 'Нужен хотя бы один из двух'}</span>
              </div>
              <div className={`trainer-helper-list__item${applicationForm.bio.trim() ? ' is-complete' : ''}`}>
                <strong>Bio</strong>
                <span>{applicationForm.bio.trim() ? 'OK' : 'Опиши специализацию'}</span>
              </div>
              <div className={`trainer-helper-list__item${normalizeDelimitedList(applicationForm.specialties_text).length ? ' is-complete' : ''}`}>
                <strong>Specialties</strong>
                <span>{normalizeDelimitedList(applicationForm.specialties_text).length ? 'OK' : 'Добавь хотя бы одну'}</span>
              </div>
            </div>

            <div className="inline">
              <button className="button secondary" type="submit" disabled={savingApplication}>
                {savingApplication ? 'Сохраняем…' : 'Сохранить draft'}
              </button>
              <button className="button" type="button" onClick={() => void submitApplication()} disabled={savingApplication || !applicationReady}>
                {savingApplication ? 'Отправляем…' : 'Отправить на модерацию'}
              </button>
            </div>
          </form>
        </section>
      </div>

      <section className="card trainer-panel">
        <div className="row trainer-panel__header">
          <div>
            <h2 className="title-md" style={{ marginBottom: 6 }}>3. Readiness roadmap</h2>
            <p className="muted">Это уже не просто TODO, а мост между trainer application, profile readiness и первой публикацией.</p>
          </div>
          <span className="badge secondary">Core loop</span>
        </div>

        <div className="trainer-roadmap-list">
          {(status?.steps || []).map((step) => {
            const isBlocked =
              step.code === 'first_publish' && applicationStatus.tone !== 'success';
            return (
              <div key={step.code} className={`trainer-roadmap-item${step.is_completed ? ' is-complete' : ''}${isBlocked ? ' is-blocked' : ''}`}>
                <div className="trainer-roadmap-item__meta">
                  <strong>{step.title}</strong>
                  <p>{step.description}</p>
                </div>
                <div className="stack" style={{ gap: 8, alignItems: 'flex-end' }}>
                  <span className={`badge ${step.is_completed ? 'success' : isBlocked ? 'warning' : 'secondary'}`}>
                    {step.is_completed ? 'Completed' : isBlocked ? 'Blocked' : 'Open'}
                  </span>
                  {step.code === 'first_publish' ? (
                    <small>Откроется после одобрения заявки и работы с видео.</small>
                  ) : null}
                </div>
              </div>
            );
          })}
        </div>
      </section>
    </div>
  );
}
