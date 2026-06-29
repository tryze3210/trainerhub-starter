'use client';

import { useEffect, useMemo, useState } from 'react';

import { ProtectedPage } from '@/components/protected-page';
import { assignmentsApi } from '@/modules/assignments/api';
import { TrainerDashboardShell } from '@/modules/trainer-dashboard/components/trainer-dashboard-shell';
import type { Assignment, AssignmentReviewPayload, AssignmentSubmission, AssignmentsPayload, AssignmentSubmissionsPayload } from '@/types/api';

const defaultForm = {
  title: '',
  description: '',
  content_type: 'course',
  content_id: '',
  lesson_id: '',
};

function formatDateTime(value?: string | null) {
  if (!value) return 'Дата не указана';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat('ru-RU', { dateStyle: 'medium', timeStyle: 'short' }).format(date);
}

function shortId(value?: string | null) {
  if (!value) return 'не указан';
  return value.length > 10 ? `ID: ${value.slice(0, 6)}…${value.slice(-3)}` : `ID: ${value}`;
}

function mapContentTypeLabel(value?: string | null) {
  if (value === 'course') return 'Курс';
  if (value === 'program') return 'Программа';
  if (value === 'video') return 'Видео';
  if (value === 'product') return 'Продукт';
  if (value === 'lesson') return 'Урок';
  return 'Материал';
}

function mapAssignmentStatusLabel(value?: string | null) {
  if (value === 'draft') return 'Черновик';
  if (value === 'published') return 'Опубликовано';
  if (value === 'archived') return 'В архиве';
  return 'Требуется проверка';
}

function mapSubmissionStatusLabel(value?: string | null) {
  if (value === 'submitted') return 'На проверке';
  if (value === 'needs_revision') return 'Нужна доработка';
  if (value === 'reviewed') return 'Проверено';
  if (value === 'approved') return 'Принято';
  if (value === 'rejected') return 'Отклонено';
  return 'Требуется проверка';
}

function getBadgeTone(value?: string | null) {
  if (['published', 'approved', 'reviewed'].includes(value || '')) return 'success';
  if (['submitted', 'needs_revision', 'draft'].includes(value || '')) return 'warning';
  if (['archived', 'rejected'].includes(value || '')) return 'danger';
  return 'neutral';
}

function badgeClass(value?: string | null) {
  return `trainer-education-status trainer-education-status-${getBadgeTone(value)}`;
}

function KpiCard({ label, value, hint }: { label: string; value: string | number; hint?: string }) {
  return (
    <article className="trainer-education-kpi-card">
      <span>{label}</span>
      <strong>{value}</strong>
      {hint ? <small>{hint}</small> : null}
    </article>
  );
}

function AssignmentCard({ assignment }: { assignment: Assignment }) {
  return (
    <article className="trainer-education-assignment-card">
      <div className="trainer-education-row">
        <div>
          <strong>{assignment.title}</strong>
          <p className="trainer-education-muted">{mapContentTypeLabel(assignment.content_type)} · {shortId(assignment.content_id)}</p>
        </div>
        <span className={badgeClass(assignment.status)}>{mapAssignmentStatusLabel(assignment.status)}</span>
      </div>
      <p>{assignment.description || 'Описание задания пока не заполнено.'}</p>
      <div className="trainer-education-row">
        <span>{assignment.submissions_count || 0} ответов</span>
        {assignment.lesson_id ? <small className="trainer-education-muted">Урок: {shortId(assignment.lesson_id)}</small> : null}
      </div>
    </article>
  );
}

export default function TrainerAssignmentsPage() {
  const [assignments, setAssignments] = useState<AssignmentsPayload | null>(null);
  const [submissions, setSubmissions] = useState<AssignmentSubmissionsPayload | null>(null);
  const [form, setForm] = useState(defaultForm);
  const [reviewDrafts, setReviewDrafts] = useState<Record<string, AssignmentReviewPayload>>({});
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState('');

  async function load() {
    setLoading(true);
    setMessage('');
    try {
      const [assignmentPayload, submissionPayload] = await Promise.all([
        assignmentsApi.getTrainerAssignments(),
        assignmentsApi.getTrainerSubmissions(),
      ]);
      setAssignments(assignmentPayload);
      setSubmissions(submissionPayload);
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Не удалось загрузить задания');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  const pendingSubmissions = useMemo(
    () => (submissions?.items || []).filter((item) => item.status === 'submitted' || item.status === 'needs_revision'),
    [submissions]
  );

  async function createAssignment() {
    setMessage('');
    try {
      await assignmentsApi.createAssignment({
        ...form,
        content_type: form.content_type as 'course' | 'program',
        status: 'published',
      });
      setForm(defaultForm);
      await load();
      setMessage('Задание опубликовано.');
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Не удалось создать задание');
    }
  }

  async function reviewSubmission(submission: AssignmentSubmission) {
    const draft = reviewDrafts[submission.id] || {};
    setMessage('');
    try {
      await assignmentsApi.reviewSubmission(submission.id, {
        status: draft.status || 'reviewed',
        review_comment: draft.review_comment || '',
        score: draft.score || null,
      });
      await load();
      setMessage('Проверка сохранена.');
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Не удалось сохранить проверку');
    }
  }

  function patchReview(id: string, patch: AssignmentReviewPayload) {
    setReviewDrafts((current) => ({
      ...current,
      [id]: {
        ...current[id],
        ...patch,
      },
    }));
  }

  return (
    <ProtectedPage title="Задания" description="Раздел заданий доступен только тренеру.">
      <TrainerDashboardShell
        title="Задания"
        description="Домашние работы, ответы учеников и проверка прогресса."
      >
        <section className="trainer-education-workbench">
          <section className="trainer-education-hero">
            <div>
              <h2>Задания</h2>
              <p>Домашние работы, ответы учеников и проверка прогресса.</p>
            </div>
            <div className="trainer-education-hero-total">
              <span>Ответы на проверку</span>
              <strong>{pendingSubmissions.length}</strong>
              <small>{assignments?.summary.total || 0} заданий · {assignments?.summary.published || 0} опубликовано · {submissions?.summary.total || 0} ответов</small>
            </div>
          </section>

          {message ? <div className="trainer-education-message"><strong>Статус</strong><p>{message}</p></div> : null}
          {loading ? <div className="trainer-education-message"><strong>Загружаем задания</strong><p>Получаем список домашних работ и ответы учеников.</p></div> : null}

          <section className="trainer-education-kpi-grid" aria-label="Показатели заданий">
            <KpiCard label="Заданий" value={assignments?.summary.total || 0} />
            <KpiCard label="Опубликовано" value={assignments?.summary.published || 0} />
            <KpiCard label="Ответов" value={submissions?.summary.total || 0} />
            <KpiCard label="На проверку" value={pendingSubmissions.length} />
            <KpiCard label="Требуют доработки" value={submissions?.summary.needs_revision || 0} />
          </section>

          <section className="trainer-education-layout">
            <div className="trainer-education-main">
              <article className="trainer-education-form-card">
                <h3>Новое задание</h3>
                <label className="trainer-education-field">
                  <span>Название задания</span>
                  <input value={form.title} onChange={(event) => setForm((prev) => ({ ...prev, title: event.target.value }))} placeholder="Например: Разбор техники" />
                </label>
                <label className="trainer-education-field">
                  <span>Описание и критерии</span>
                  <textarea rows={4} value={form.description} onChange={(event) => setForm((prev) => ({ ...prev, description: event.target.value }))} placeholder="Что нужно сделать ученику и как будет оцениваться ответ" />
                </label>
                <label className="trainer-education-field">
                  <span>Тип материала</span>
                  <select value={form.content_type} onChange={(event) => setForm((prev) => ({ ...prev, content_type: event.target.value }))}>
                    <option value="course">Курс</option>
                    <option value="program">Программа</option>
                  </select>
                </label>
                <label className="trainer-education-field">
                  <span>Связанный материал</span>
                  <input value={form.content_id} onChange={(event) => setForm((prev) => ({ ...prev, content_id: event.target.value }))} placeholder="ID курса или программы" />
                  <small className="trainer-education-muted">Пока используется внутренний ID курса или программы. Позже здесь будет выбор из библиотеки.</small>
                </label>
                <label className="trainer-education-field">
                  <span>Урок внутри материала</span>
                  <input value={form.lesson_id} onChange={(event) => setForm((prev) => ({ ...prev, lesson_id: event.target.value }))} placeholder="Необязательная связь с уроком" />
                  <small className="trainer-education-muted">Необязательно. Нужен только если задание связано с конкретным уроком.</small>
                </label>
                <div className="trainer-education-actions">
                  <button className="premium-primary-button" onClick={() => void createAssignment()} type="button">Опубликовать задание</button>
                </div>
              </article>

              <article className="trainer-education-panel">
                <h3>Ответы учеников</h3>
                {(submissions?.items || []).map((submission) => {
                  const draft = reviewDrafts[submission.id] || {};
                  return (
                    <article className="trainer-education-submission-card" key={submission.id}>
                      <div className="trainer-education-row">
                        <div>
                          <strong>{submission.assignment?.title || 'Задание'}</strong>
                          <p>{submission.student_email || 'Ученик'} · {formatDateTime(submission.submitted_at)}</p>
                        </div>
                        <span className={badgeClass(submission.status)}>{mapSubmissionStatusLabel(submission.status)}</span>
                      </div>
                      <p>{submission.answer_text || 'Ответ без текста.'}</p>
                      <div className="trainer-education-form-card">
                        <label className="trainer-education-field">
                          <span>Статус проверки</span>
                          <select value={draft.status || submission.status || 'reviewed'} onChange={(event) => patchReview(submission.id, { status: event.target.value as AssignmentReviewPayload['status'] })}>
                            <option value="reviewed">Проверено</option>
                            <option value="needs_revision">Нужна доработка</option>
                            <option value="approved">Принято</option>
                          </select>
                        </label>
                        <label className="trainer-education-field">
                          <span>Оценка</span>
                          <input value={draft.score ?? submission.score ?? ''} onChange={(event) => patchReview(submission.id, { score: event.target.value })} placeholder="Например: 85" />
                        </label>
                        <label className="trainer-education-field">
                          <span>Комментарий ученику</span>
                          <textarea rows={3} value={draft.review_comment ?? submission.review_comment ?? ''} onChange={(event) => patchReview(submission.id, { review_comment: event.target.value })} placeholder="Что получилось и что улучшить" />
                        </label>
                        <div className="trainer-education-actions">
                          <button className="premium-secondary-button" onClick={() => void reviewSubmission(submission)} type="button">
                            Сохранить проверку
                          </button>
                        </div>
                      </div>
                    </article>
                  );
                })}
                {!submissions?.items.length ? (
                  <div className="trainer-education-empty">
                    <strong>Ответов пока нет</strong>
                    <p>Ответов пока нет. Они появятся после публикации заданий и прохождения уроков учениками.</p>
                  </div>
                ) : null}
              </article>
            </div>

            <aside className="trainer-education-sidebar">
              <article className="trainer-education-panel">
                <h3>Опубликованные задания</h3>
                {(assignments?.items || []).map((assignment) => <AssignmentCard assignment={assignment} key={assignment.id} />)}
                {!assignments?.items.length ? (
                  <div className="trainer-education-empty">
                    <strong>Заданий пока нет</strong>
                    <p>Создайте первое задание и привяжите его к курсу или программе.</p>
                  </div>
                ) : null}
              </article>
            </aside>
          </section>
        </section>
      </TrainerDashboardShell>
    </ProtectedPage>
  );
}
